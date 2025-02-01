import os
import sys

# Agregar el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import ccxt
import pandas as pd
import logging
from agents.detection_agent import DetectionAgent

def get_exchange():
    return ccxt.binance()  # or your preferred exchange configuration

def fetch_market_data(symbol, timeframe, limit=1000):
    """
    Obtiene datos OHLCV y calcula VWAP diario desde la 1 AM
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
            # Si el símbolo es 'BTCUSDT', convertirlo a 'BTC/USDT'
            symbol = f"{symbol[:-4]}/{symbol[-4:]}" if symbol.endswith('USDT') else f"{symbol[:-3]}/{symbol[-3:]}"
        
        # Verificar que el mercado existe
        exchange.load_markets()
        if symbol not in exchange.markets:
            raise Exception(f"Symbol {symbol} no encontrado en Binance")

        print(f"Fetching {limit} candles with {timeframe} timeframe for {symbol}")
        
        # Obtener datos directamente con ccxt
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit + 288)
        if not ohlcv:
            raise Exception("No se recibieron datos de Binance")
            
        print(f"Received {len(ohlcv)} candles")
        
        # Crear DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)
        
        # Calcular Daily VWAP desde 1 AM
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['TPV'] = df['typical_price'] * df['volume']
        
        # Crear grupos por día comenzando a la 1 AM
        df['trading_day'] = df.index.map(lambda x: 
            x.date() if x.hour >= 1 else 
            (x - pd.Timedelta(days=1)).date())
        
        # Calcular VWAP por día de trading (1 AM - 1 AM)
        df['cum_TPV'] = df.groupby('trading_day')['TPV'].cumsum()
        df['cum_vol'] = df.groupby('trading_day')['volume'].cumsum()
        df['VWAP'] = df['cum_TPV'] / df['cum_vol']
        
        # Limpiar y mantener solo las últimas velas solicitadas
        df = df[['open', 'high', 'low', 'close', 'volume', 'VWAP']]
        df = df.tail(limit)

        print(f"Timeframe: {timeframe}")
        print("Timestamps range:", df.index.min(), "to", df.index.max())
        print("\nPrimeras 5 velas con VWAP diario (1 AM reset):")
        print(df[['close', 'VWAP']].head())
        print("\nÚltimas 5 velas con VWAP diario (1 AM reset):")
        print(df[['close', 'VWAP']].tail())

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