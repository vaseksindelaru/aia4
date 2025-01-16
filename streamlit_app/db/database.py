import pandas as pd
from sqlalchemy import create_engine, text
import logging

class Database:
    def __init__(self, db_user, db_password, db_host, db_database, table_name):
        self.engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_database}")
        self.table_name = table_name
        self.create_table_if_not_exists()
        self.create_adjustment_results_table()

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

    def create_adjustment_results_table(self):
        """
        Crea la tabla adjustment_results si no existe.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS adjustment_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            parameter_name VARCHAR(255),
            parameter_value FLOAT,
            app_selection_count INT,
            user_selection_count INT,
            similarity_score FLOAT
        );
        """
        with self.engine.connect() as connection:
            connection.execute(text(create_table_query))

    def create_user_selection_table(self):
        """
        Crea la tabla user_selections si no existe.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_selections (
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

    def save_adjustment_result(self, parameter_name, parameter_value, app_selection_count, user_selection_count, similarity_score):
        """
        Guarda los resultados del ajuste en la base de datos.
        """
        insert_query = f"""
        INSERT INTO adjustment_results (parameter_name, parameter_value, app_selection_count, user_selection_count, similarity_score)
        VALUES ('{parameter_name}', {parameter_value}, {app_selection_count}, {user_selection_count}, {similarity_score});
        """
        with self.engine.connect() as connection:
            connection.execute(text(insert_query))

    def save_user_selection(self, df):
        """
        Guarda la selección del usuario en la base de datos.
        """
        try:
            df.to_sql('user_selections', self.engine, if_exists='append', index=False)
        except Exception as e:
            logging.error(f"Error al guardar la selección del usuario en la base de datos: {e}")
            raise