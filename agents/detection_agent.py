import pandas as pd
from streamlit_app.db.database import Database

class DetectionAgent:
    def __init__(self, db_user, db_password, db_host, db_database, table_name):
        self.db = Database(db_user, db_password, db_host, db_database, table_name)

    def detect(self, df):
        """
        Filtra las velas con volumen mayor al promedio y tamaño menor al promedio.
        """
        df['Total_Height'] = df['high'] - df['low']
        df['Volume_SMA'] = df['volume'].rolling(window=5).mean()
        df['Total_Height_SMA'] = df['Total_Height'].rolling(window=5).mean()

        df['High_Volume'] = df['volume'] > df['Volume_SMA']
        df['Small_Body'] = df['Total_Height'] < df['Total_Height_SMA']

        df_filtered = df[df['High_Volume'] & df['Small_Body']].copy()
        df_filtered = df_filtered.apply(pd.to_numeric, errors='coerce')
        self.db.save_to_db(df_filtered)
        return df_filtered