import pandas as pd
from sqlalchemy import create_engine, text
import logging

class Database:
    def __init__(self, db_user, db_password, db_host, db_database, table_name):
        self.engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_database}")
        self.table_name = table_name
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        """
        Crea la tabla si no existe.
        """
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            timestamp DATETIME,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume FLOAT,
            Total_Height FLOAT,
            Volume_SMA FLOAT,
            Total_Height_SMA FLOAT,
            High_Volume BOOLEAN,
            Small_Body BOOLEAN
        );
        """
        with self.engine.connect() as connection:
            connection.execute(text(create_table_query))

    def save_to_db(self, df):
        """
        Guarda el DataFrame en la base de datos.
        """
        try:
            df.to_sql(self.table_name, self.engine, if_exists='append', index=False)
        except Exception as e:
            logging.error(f"Error al guardar en la base de datos: {e}")
            raise