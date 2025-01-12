import streamlit as st
import pandas as pd
from agents.detection_agent import DetectionAgent
from streamlit_app.components.charts import plot_candlestick_chart
from streamlit_app.utils.market_data import fetch_market_data, process_market_data

# Configuración de la conexión a la base de datos MySQL
db_user = 'root'
db_password = '21blackjack'
db_host = 'localhost'
db_database = 'sql1'
table_name = 'app_selections'

def main():
    st.title("Análisis de Velas y Detección de Rebotes")

    # Configuración del mercado
    symbol = st.text_input("Par de trading (e.g., BTC/USDT):", "BTC/USDT")
    timeframe = st.selectbox("Intervalo de tiempo:", ["1m", "5m", "15m", "1h", "1d"], index=1)
    limit = st.slider("Cantidad de velas:", 10, 100, 50)

    if st.button("Obtener datos"):
        with st.spinner("Obteniendo datos del mercado..."):
            market_data = fetch_market_data(symbol, timeframe, limit)
            if market_data.empty:
                st.error("No se pudieron obtener datos del mercado. Verifique los parámetros.")
                return

        st.subheader("Datos de mercado")
        st.write(market_data)

        with st.spinner("Procesando datos con el agente de detección..."):
            detection_agent = DetectionAgent(db_user, db_password, db_host, db_database, table_name)
            detected = detection_agent.detect(market_data)
            st.subheader("Velas detectadas")
            st.write(detected)

        # Asegúrate de que los datos sean del tipo correcto
        market_data = market_data.apply(pd.to_numeric, errors='coerce')
        detected = detected.apply(pd.to_numeric, errors='coerce')

        st.subheader("Gráfico de velas")
        fig = plot_candlestick_chart(market_data, detected)
        st.pyplot(fig)

if __name__ == "__main__":
   main()