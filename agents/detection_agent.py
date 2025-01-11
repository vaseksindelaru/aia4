import pandas as pd

class DetectionAgent:
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
        return df_filtered