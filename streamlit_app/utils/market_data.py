import os
import sys

# Agregar el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import ccxt
import pandas as pd
import logging
from agents.detection_agent import DetectionAgent

# Configuración del exchange y parámetros
exchange = ccxt.binance()

def fetch_market_data(symbol, timeframe, limit):
    """
    Obtiene datos OHLCV del exchange usando ccxt.
    """
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
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