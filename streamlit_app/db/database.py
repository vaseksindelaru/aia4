import pandas as pd
from sqlalchemy import create_engine, text
import logging

class Database:
    def __init__(self, db_user, db_password, db_host, db_database, table_name):
        self.engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_database}")
        self.table_name = table_name
        self.create_table_if_not_exists()
        self.create_adjustment_results_table()
        self.create_user_selection_table()
        self.create_prediction_user_table()
        self.create_prediction_example_table()

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
            VWAP FLOAT,
            VWAP_upper FLOAT,
            VWAP_lower FLOAT,
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
            VWAP FLOAT,
            VWAP_upper FLOAT,
            VWAP_lower FLOAT,
            Total_Height FLOAT,
            Volume_SMA FLOAT,
            Total_Height_SMA FLOAT,
            High_Volume BOOLEAN,
            Small_Body BOOLEAN
        );
        """
        with self.engine.connect() as connection:
            connection.execute(text(create_table_query))

    def create_prediction_user_table(self):
        """
        Crea la tabla prediction_user si no existe.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS prediction_user (
            timestamp DATETIME,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume FLOAT,
            VWAP FLOAT,
            VWAP_upper FLOAT,
            VWAP_lower FLOAT,
            Total_Height FLOAT,
            Volume_SMA FLOAT,
            Total_Height_SMA FLOAT,
            High_Volume BOOLEAN,
            Small_Body BOOLEAN
        );
        """
        with self.engine.connect() as connection:
            connection.execute(text(create_table_query))

    def create_prediction_example_table(self):
        """
        Crea la tabla prediction_example si no existe.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS prediction_example (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inicial_price FLOAT,
            rebote_close FLOAT,
            promedio_velas_siguientes FLOAT,
            signo VARCHAR(2),
            exito_rebote VARCHAR(2),
            UNIQUE INDEX idx_unique_prediction (inicial_price, rebote_close, promedio_velas_siguientes)
        );
        """
        with self.engine.connect() as connection:
            connection.execute(text(create_table_query))

    def fetch_table_data(self, table_name):
        """
        Fetch data from a specified table in the database.
        """
        query = f"SELECT * FROM {table_name}"
        try:
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            logging.error(f"Error al obtener datos de la tabla {table_name}: {e}")
            return pd.DataFrame()

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

    def save_user_selection(self, df, table_name='user_selections'):
        """
        Guarda la selección del usuario en la base de datos.
        """
        try:
            # Clear the table before saving new data
            with self.engine.connect() as connection:
                connection.execute(text(f"TRUNCATE TABLE {table_name}"))

            # Save the new data
            df.to_sql(table_name, self.engine, if_exists='append', index=False)
        except Exception as e:
            logging.error(f"Error al guardar la selección del usuario en la base de datos: {e}")
            raise

    def save_prediction_user(self, df):
        """
        Guarda la selección del usuario en la tabla prediction_user.
        """
        try:
            df.to_sql('prediction_user', self.engine, if_exists='append', index=False)
        except Exception as e:
            logging.error(f"Error al guardar la selección del usuario en la tabla prediction_user: {e}")
            raise

    def clear_user_selection(self):
        """
        Borra el contenido de la tabla user_selections.
        """
        clear_table_query = "TRUNCATE TABLE user_selections;"
        with self.engine.connect() as connection:
            connection.execute(text(clear_table_query))

    def recreate_tables(self):
        """
        Elimina y vuelve a crear todas las tablas.
        """
        drop_queries = [
            f"DROP TABLE IF EXISTS {self.table_name}",
            "DROP TABLE IF EXISTS user_selections",
            "DROP TABLE IF EXISTS prediction_user"
        ]
        
        with self.engine.connect() as connection:
            for query in drop_queries:
                connection.execute(text(query))
            connection.commit()
        
        # Recrear las tablas
        self.create_table_if_not_exists()
        self.create_user_selection_table()
        self.create_prediction_user_table()