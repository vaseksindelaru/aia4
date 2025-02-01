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
    Obtiene datos OHLCV y calcula VWAP
    """
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
            }
        })
        
        # Calcular número de velas necesarias
        candles_per_day = min(1000, int((24 * 60) / int(timeframe[:-1])))
        print(f"Fetching {candles_per_day} candles for VWAP calculation")
        
        # Usar el método estándar de CCXT
        ohlcv = exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=candles_per_day
        )
        
        if not ohlcv:
            raise Exception("No data received from exchange")
            
        print(f"Received {len(ohlcv)} candles from exchange")
        
        # Crear DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convertir timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)
        
        # Calcular VWAP desde el inicio del día
        df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
        df['TPV'] = df['Typical_Price'] * df['volume']
        df['VWAP'] = df['TPV'].cumsum() / df['volume'].cumsum()
        
        # Mantener solo las últimas 'limit' velas para la visualización
        df = df.tail(limit)
        
        # Mantener solo las columnas necesarias
        df = df[['open', 'high', 'low', 'close', 'volume', 'VWAP']]

        print(f"Timeframe: {timeframe}")
        print("Timestamps range:", df.index.min(), "to", df.index.max())
        print("\nPrimeras 5 velas del período mostrado:")
        print(df[['close', 'VWAP']].head())
        print("\nÚltimas 5 velas:")
        print(df[['close', 'VWAP']].tail())

        return df
    except Exception as e:
        logging.error(f"Error al obtener datos de mercado: {str(e)}")
        raise  # Propagar el error para mejor diagnóstico

def process_market_data(df):
    """
    Procesa los datos con el agente de detección.
    """
    detection_agent = DetectionAgent()
    filtered_data = detection_agent.detect(df)
    return filtered_data