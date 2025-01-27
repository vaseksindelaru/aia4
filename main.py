# main.py
from streamlit_app.utils.market_data import fetch_market_data, process_market_data
import logging

# Configuración
SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"
LIMIT = 50

def main():
    logging.info("Obteniendo datos de mercado...")
    market_data = fetch_market_data(SYMBOL, TIMEFRAME, LIMIT)

    if market_data.empty:
        logging.warning("No se obtuvieron datos de mercado.")
        return

    logging.info("Procesando datos con el agente de detección...")
    filtered_data = process_market_data(market_data)

    logging.info("Datos procesados:")
    print(filtered_data)

if __name__ == "__main__":
    main()
