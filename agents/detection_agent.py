import pandas as pd
from sqlalchemy import exc, text

class DetectionAgent:
    def __init__(self, db):
        self.db = db

    def calcular_exito_rebote(self, promedio_siguiente, rebote_close, inicial_price, signo_intermedias):
        # Implement your logic to calculate exito_rebote
        return "+" if promedio_siguiente > rebote_close else "-"

    def detect(self, df, volume_sma_window=5, height_sma_window=5):
        """
        Filtra las velas con volumen mayor al promedio y tamaño menor al promedio.
        """
        df['Total_Height'] = df['high'] - df['low']
        df['Volume_SMA'] = df['volume'].rolling(window=volume_sma_window).mean()
        df['Total_Height_SMA'] = df['Total_Height'].rolling(window=height_sma_window).mean()

        df['High_Volume'] = df['volume'] > df['Volume_SMA']
        df['Small_Body'] = df['Total_Height'] < df['Total_Height_SMA']

        df_filtered = df[df['High_Volume'] & df['Small_Body']].copy()
        df_filtered = df_filtered.apply(pd.to_numeric, errors='coerce')
        self.db.save_to_db(df_filtered)
        return df_filtered

    def detectar_rebotes_con_intermedias(self, df, index, intermedias_window=1):
        """
        Detecta rebotes con al menos una vela intermedia.
        """
        vela_i = df.iloc[index]
        promedio_precio = (vela_i['high'] + vela_i['low']) / 2
        direccion = 'alcista' if vela_i['close'] > vela_i['open'] else 'bajista'

        for i in range(index + intermedias_window + 1, len(df)):  # Se asegura al menos una vela intermedia
            vela_actual = df.iloc[i]
            if vela_actual['low'] <= promedio_precio <= vela_actual['high']:
                if direccion == 'alcista' and vela_actual['close'] > promedio_precio:
                    return i
                elif direccion == 'bajista' and vela_actual['close'] < promedio_precio:
                    return i
        return None

    def guardar_en_base_datos(self, df, index_pos, rebote_index, promedio_siguiente, signo_intermedias, candle_id):
        """
        Guarda los datos en la base de datos reescribiendo los existentes.
        """
        try:
            with self.db.engine.connect() as connection:
                # Clear the table before inserting new data
                connection.execute(text("TRUNCATE TABLE prediction_example"))

                # Ensure indices are valid
                if index_pos < 0 or index_pos >= len(df) or rebote_index < 0 or rebote_index >= len(df):
                    print("Invalid index positions for data extraction.")
                    return

                # Extract data
                rebote_close = df['close'].iloc[rebote_index]
                inicial_price = df['close'].iloc[index_pos]
                exito_rebote = self.calcular_exito_rebote(promedio_siguiente, rebote_close, inicial_price, signo_intermedias)

                # Get additional data
                timestamp = df.index[index_pos]
                open_price = df['open'].iloc[index_pos]
                high_price = df['high'].iloc[index_pos]
                low_price = df['low'].iloc[index_pos]
                volume = df['volume'].iloc[index_pos]

                # Debugging: Print extracted values
                print(f"Extracted Data - Timestamp: {timestamp}, Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {rebote_close}, Volume: {volume}")

                # Ensure no None values are inserted
                if pd.isnull([timestamp, open_price, high_price, low_price, rebote_close, inicial_price, volume]).any():
                    print("Detected None or NaN values in the data.")
                    return

                query = text("""
                INSERT INTO prediction_example (candle_id, timestamp, open, high, low, close, volume, inicial_price, rebote_close, promedio_velas_siguientes, signo, exito_rebote)
                VALUES (:candle_id, :timestamp, :open, :high, :low, :close, :volume, :inicial_price, :rebote_close, :promedio_velas_siguientes, :signo, :exito_rebote)
                """)

                data = {
                    "candle_id": candle_id,
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": df['close'].iloc[index_pos],
                    "volume": volume,
                    "inicial_price": inicial_price,
                    "rebote_close": rebote_close,
                    "promedio_velas_siguientes": promedio_siguiente,
                    "signo": signo_intermedias,
                    "exito_rebote": exito_rebote
                }
                connection.execute(query, data)
                connection.commit()
                print("Inserción exitosa en la base de datos con exito_rebote.")
        except exc.SQLAlchemyError as e:
            print(f"Error al guardar en la base de datos: {e}")