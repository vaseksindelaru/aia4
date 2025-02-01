import os
import sys

# Agregar el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import ccxt
import pandas as pd
import logging
from agents.detection_agent import DetectionAgent
import numpy as np

def get_exchange():
    return ccxt.binance()  # or your preferred exchange configuration

def fetch_market_data(symbol, timeframe, limit=1000):
    """
    Obtiene datos OHLCV y calcula VWAP diario desde la 1 AM con bandas de desviación
    """
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
            }
        })

        # Asegurar formato correcto del símbolo
        if '/' not in symbol:
            symbol = f"{symbol[:-4]}/{symbol[-4:]}" if symbol.endswith('USDT') else f"{symbol[:-3]}/{symbol[-3:]}"
        
        exchange.load_markets()
        if symbol not in exchange.markets:
            raise Exception(f"Symbol {symbol} no encontrado en Binance")

        print(f"Fetching {limit} candles with {timeframe} timeframe for {symbol}")
        
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit + 288)
        if not ohlcv:
            raise Exception("No se recibieron datos de Binance")
            
        print(f"Received {len(ohlcv)} candles")
        
        # Crear DataFrame base
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)
        
        # Asegurar que todas las columnas numéricas sean float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Calcular precio típico y TPV
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['TPV'] = df['typical_price'] * df['volume']
        
        # Crear grupos por día comenzando a la 1 AM
        df['trading_day'] = df.index.map(lambda x: 
            x.date() if x.hour >= 1 else 
            (x - pd.Timedelta(days=1)).date())
        
        # Inicializar columnas para VWAP y bandas
        df['VWAP'] = np.nan
        df['VWAP_upper'] = np.nan
        df['VWAP_lower'] = np.nan
        
        # Calcular VWAP y bandas por día de trading
        for day in df['trading_day'].unique():
            mask = df['trading_day'] == day
            
            # Calcular VWAP
            df.loc[mask, 'cum_TPV'] = df.loc[mask, 'TPV'].cumsum()
            df.loc[mask, 'cum_vol'] = df.loc[mask, 'volume'].cumsum()
            df.loc[mask, 'VWAP'] = df.loc[mask, 'cum_TPV'] / df.loc[mask, 'cum_vol']
            
            # Calcular desviación estándar
            df.loc[mask, 'squared_diff'] = (df.loc[mask, 'typical_price'] - df.loc[mask, 'VWAP']) ** 2
            df.loc[mask, 'std_dev'] = np.sqrt(df.loc[mask, 'squared_diff'].cumsum() / df.loc[mask, 'cum_vol'])
            
            # Calcular bandas
            df.loc[mask, 'VWAP_upper'] = df.loc[mask, 'VWAP'] + (1.28 * df.loc[mask, 'std_dev'])
            df.loc[mask, 'VWAP_lower'] = df.loc[mask, 'VWAP'] - (1.28 * df.loc[mask, 'std_dev'])
        
        # Limpiar columnas temporales
        columns_to_drop = ['trading_day', 'typical_price', 'TPV', 'cum_TPV', 'cum_vol', 
                          'squared_diff', 'std_dev']
        df = df.drop(columns=columns_to_drop)
        
        # Mantener solo las últimas velas solicitadas
        df = df.tail(limit)
        
        # Verificar que las columnas existan
        required_columns = ['open', 'high', 'low', 'close', 'volume', 'VWAP', 'VWAP_upper', 'VWAP_lower']
        for col in required_columns:
            if col not in df.columns:
                print(f"Missing column: {col}")
        
        print("\nColumnas en el DataFrame final:", df.columns.tolist())
        print("\nPrimeras 5 velas:")
        print(df[['close', 'VWAP', 'VWAP_upper', 'VWAP_lower']].head())

        return df
    except Exception as e:
        logging.error(f"Error al obtener datos de mercado: {str(e)}")
        logging.error(f"Symbol: {symbol}, Timeframe: {timeframe}")
        return pd.DataFrame()

def process_market_data(df):
    """
    Procesa los datos con el agente de detección.
    """
    detection_agent = DetectionAgent()
    filtered_data = detection_agent.detect(df)
    return filtered_data