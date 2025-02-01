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
    
    # Asegurarse de que todas las columnas necesarias estén presentes
    columns_to_save = ['open', 'high', 'low', 'close', 'volume', 'VWAP', 'VWAP_upper', 'VWAP_lower',
                      'Total_Height', 'Volume_SMA', 'Total_Height_SMA', 'High_Volume', 'Small_Body']
    
    df_filtered = df_filtered[columns_to_save]
    df_filtered = df_filtered.apply(pd.to_numeric, errors='coerce')
    
    self.db.save_to_db(df_filtered)
    return df_filtered 