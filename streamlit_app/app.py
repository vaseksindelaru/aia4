import streamlit as st
import pandas as pd
from agents.detection_agent import DetectionAgent
from agents.adjust_agent import AdjustAgent
from streamlit_app.components.charts import plot_candlestick_chart
from streamlit_app.db.database import Database  # Correct import
from utils.market_data import fetch_market_data
from sqlalchemy import text

db_user = 'root'
db_password = '21blackjack'
db_host = 'localhost'
db_database = 'sql1'
table_name = 'prediction_results'
example_table_name = 'prediction_example'
user_selection_table_name = 'user_selections'

def main():
    st.title("Análisis de Velas y Detección de Rebotes")

    # Configuración del mercado
    symbol = st.text_input("Par de trading (e.g., BTC/USDT):", "BTC/USDT")
    timeframe = st.selectbox("Intervalo de tiempo:", ["1m", "5m", "15m", "1h", "1d"], index=1)
    limit = st.slider("Cantidad de velas:", 10, 100, 50)

    detection_agent = DetectionAgent(db_user, db_password, db_host, db_database, table_name)
    adjust_agent = AdjustAgent(db_user, db_password, db_host, db_database)
    database = Database(db_user, db_password, db_host, db_database, table_name)

    # Initialize session state keys if they do not exist
    if 'market_data' not in st.session_state:
        st.session_state['market_data'] = None
    if 'detected' not in st.session_state:
        st.session_state['detected'] = None
    if 'selected_example_indices' not in st.session_state:
        st.session_state['selected_example_indices'] = []

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
            # Clear the prediction_example table before processing new data
            with database.engine.connect() as connection:
                connection.execute(text("TRUNCATE TABLE prediction_example"))

            detected = detection_agent.detect(st.session_state['market_data'])
            st.session_state['detected'] = detected

        st.subheader("Velas detectadas")
        st.write(st.session_state['detected'])

        # Asegúrate de que los datos sean del tipo correcto
        st.session_state['market_data'] = st.session_state['market_data'].apply(pd.to_numeric, errors='coerce')
        st.session_state['detected'] = st.session_state['detected'].apply(pd.to_numeric, errors='coerce')

        st.subheader("Gráfico de velas")
        fig = plot_candlestick_chart(st.session_state['market_data'], st.session_state['detected'], detection_agent)
        st.pyplot(fig)

        # Fetch and display the current data from prediction_example table
        example_data = database.fetch_table_data(example_table_name)
        if example_data.empty:
            st.error("No se pudieron obtener datos de ejemplo. Verifique la tabla de la base de datos.")
        else:
            st.session_state['example_data'] = example_data
            st.subheader("Datos de la tabla de predicción")
            st.write(st.session_state['example_data'])

    if 'example_data' in st.session_state:
        st.subheader("Selecciona las filas de ejemplo")
        
        # Initialize selected_example_indices in session state if not present
        if 'selected_example_indices' not in st.session_state:
            st.session_state['selected_example_indices'] = []

        # Use a callback to update the session state when the selection changes
        def update_selection():
            st.session_state['selected_example_indices'] = st.session_state['selected_indices']

        # Create a multiselect widget with a callback
        selected_example_indices = st.multiselect(
            "Selecciona las filas de ejemplo",
            st.session_state['example_data'].index,
            default=st.session_state['selected_example_indices'],
            key='selected_indices',
            on_change=update_selection
        )

        selected_example_rows = st.session_state['example_data'].loc[st.session_state['selected_example_indices']]

        st.subheader("Filas seleccionadas")
        st.write(selected_example_rows)

        st.subheader("Gráfico de velas")
        fig = plot_candlestick_chart(st.session_state['market_data'], st.session_state['detected'], detection_agent)
        st.pyplot(fig)

        if st.button("Guardar selección"):
            # Save the selected example rows to a new table
            try:
                selected_example_rows.to_sql('selected_examples', database.engine, if_exists='append', index=False)
                st.success("Selección guardada en la base de datos (selected_examples)")
            except Exception as e:
                st.error(f"Error al guardar la selección en la base de datos: {e}")

            # Clear the selected indices after saving
            st.session_state['selected_example_indices'] = []

            # Optimizar parámetros automáticamente después de guardar la selección
            best_params, best_similarity_score = adjust_agent.optimize_parameters(detection_agent, st.session_state['market_data'], selected_example_rows)
            st.write(f"Mejores parámetros: {best_params}")
            st.write(f"Mejor puntuación de similitud: {best_similarity_score}")

if __name__ == "__main__":
   main()