# filepath: /c:/Users/vaclav/aia4/streamlit_app/app.py
import streamlit as st
from agents.detection_agent import DetectionAgent
from streamlit_app.components.charts import plot_candlestick_chart
from streamlit_app.utils.market_data import fetch_market_data, process_market_data

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
            detected = process_market_data(market_data)
            st.subheader("Velas detectadas")
            st.write(detected)

        st.subheader("Gráfico de velas")
        fig = plot_candlestick_chart(market_data, detected)
        st.pyplot(fig)

if __name__ == "__main__":
   main()