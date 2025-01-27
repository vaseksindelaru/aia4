import pandas as pd
from streamlit_app.db.database import Database
from sqlalchemy.sql import text
from sqlalchemy import exc

class DetectionAgent:
    def __init__(self, db_user, db_password, db_host, db_database, table_name):
        self.db = Database(db_user, db_password, db_host, db_database, table_name)
        self.db.create_user_selection_table()
        self.db.create_prediction_user_table()

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

    def promedio_dos_velas_siguientes(self, df, index, siguientes_window=2):
        """
        Calcula el promedio de las dos velas siguientes.
        """
        if index + siguientes_window < len(df):
            promedio_siguiente = df['close'].iloc[index + 1:index + siguientes_window + 1].mean()
            return promedio_siguiente
        return None

    def promedio_velas_intermedias(self, df, index_start, index_end):
        """
        Calcula el promedio de velas intermedias.
        """
        if index_start + 1 < index_end:
            velas_intermedias = df.iloc(index_start + 1:index_end)
            return velas_intermedias['close'].mean()
        return None

    def calcular_exito_rebote(self, promedio_siguiente, rebote_close, inicial_price, signo):
        """
        Calcula el éxito del rebote.
        """
        if (promedio_siguiente > rebote_close and rebote_close > inicial_price and signo == "-") or \
           (promedio_siguiente < rebote_close and rebote_close < inicial_price and signo == "+"):
            return "-"
        elif (promedio_siguiente < rebote_close and signo == "-") or \
             (promedio_siguiente > rebote_close and signo == "+"):
            return "+"
        elif (promedio_siguiente < rebote_close and rebote_close > promedio_siguiente and signo == "-") or \
             (promedio_siguiente > rebote_close and rebote_close < promedio_siguiente and signo == "+"):
            return "++"
        return None

    def guardar_en_base_datos(self, df, index_pos, rebote_index, promedio_siguiente, signo_intermedias):
        """
        Guarda los datos en la base de datos.
        """
        try:
            with self.db.engine.connect() as connection:
                rebote_close = df['close'].iloc[rebote_index]
                inicial_price = df['close'].iloc[index_pos]
                exito_rebote = self.calcular_exito_rebote(promedio_siguiente, rebote_close, inicial_price, signo_intermedias)

                query = text("""
                INSERT INTO prediction_example (inicial_price, rebote_close, promedio_velas_siguientes, signo, exito_rebote)
                VALUES (:inicial_price, :rebote_close, :promedio_velas_siguientes, :signo, :exito_rebote)
                """)

                data = {
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

    def save_user_selection(self, df):
        """
        Guarda la selección del usuario en la base de datos.
        """
        self.db.save_prediction_user(df)