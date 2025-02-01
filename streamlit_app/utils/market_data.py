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
    Obtiene datos OHLCV del exchange usando ccxt.
    """
    try:
        exchange = get_exchange()
        # Validar timeframe
        valid_timeframes = ['1m', '5m', '15m', '1h', '1d']
        if timeframe not in valid_timeframes:
            timeframe = '5m'  # default to 5m if invalid
        
        print(f"Fetching {limit} candles with {timeframe} timeframe")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)

        # Calculate VWAP
        q = df['volume']
        p = (df['high'] + df['low'] + df['close']) / 3
        df['VWAP'] = (p * q).cumsum() / q.cumsum()

        df = df.sort_index()
        print(f"Timeframe: {timeframe}")
        print("Timestamps range:", df.index.min(), "to", df.index.max())
        print(df[['close', 'VWAP']].head())

        return df
    except Exception as e:
        logging.error(f"Error al obtener datos de mercado: {e}")
        return pd.DataFrame()

def process_market_data(df):
    """
    Procesa los datos con el agente de detección.
    """
    detection_agent = DetectionAgent()
    filtered_data = detection_agent.detect(df)
    return filtered_data