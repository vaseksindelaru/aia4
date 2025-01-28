// ... existing code ...

def guardar_en_base_datos(self, df, index_pos, rebote_index, promedio_siguiente, signo_intermedias):
    """
    Guarda los datos en la base de datos reescribiendo los existentes.
    """
    try:
        with self.db.engine.connect() as connection:
            # Clear the table before inserting new data
            connection.execute(text("TRUNCATE TABLE prediction_example"))

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

// ... existing code ...