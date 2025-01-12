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
table_name = 'prediction_results'

def main():
    st.title("Análisis de Velas y Detección de Rebotes")

    # Configuración del mercado
    symbol = st.text_input("Par de trading (e.g., BTC/USDT):", "BTC/USDT")
    timeframe = st.selectbox("Intervalo de tiempo:", ["1m", "5m", "15m", "1h", "1d"], index=1)
    limit = st.slider("Cantidad de velas:", 10, 100, 50)

    detection_agent = DetectionAgent(db_user, db_password, db_host, db_database, table_name)

    if st.button("Obtener datos"):
        with st.spinner("Obteniendo datos del mercado..."):
            market_data = fetch_market_data(symbol, timeframe, limit)
            if market_data.empty:
                st.error("No se pudieron obtener datos del mercado. Verifique los parámetros.")
                return

            st.session_state['market_data'] = market_data

        st.subheader("Datos de mercado")
        st.write(st.session_state['market_data'])

        with st.spinner("Procesando datos con el agente de detección..."):
            detected = detection_agent.detect(st.session_state['market_data'])
            st.session_state['detected'] = detected

        st.subheader("Velas detectadas")
        st.write(st.session_state['detected'])

        # Asegúrate de que los datos sean del tipo correcto
        st.session_state['market_data'] = st.session_state['market_data'].apply(pd.to_numeric, errors='coerce')
        st.session_state['detected'] = st.session_state['detected'].apply(pd.to_numeric, errors='coerce')

        st.subheader("Gráfico de velas")
        fig = plot_candlestick_chart(st.session_state['market_data'], st.session_state['detected'])
        st.pyplot(fig)

    if 'detected' in st.session_state:
        st.subheader("Selecciona las velas detectadas que deseas guardar")
        selected_indices = st.multiselect("Selecciona las filas", st.session_state['detected'].index)
        selected_rows = st.session_state['detected'].loc[selected_indices]

        if st.button("Guardar selección"):
            detection_agent.save_user_selection(selected_rows)
            st.success("Selección guardada en la base de datos")

if __name__ == "__main__":
   main()