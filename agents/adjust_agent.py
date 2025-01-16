import pandas as pd
from streamlit_app.db.database import Database
from scipy.stats import pearsonr

class AdjustAgent:
    def __init__(self, db_user, db_password, db_host, db_database):
        self.db = Database(db_user, db_password, db_host, db_database, "adjustment_results")

    def optimize_parameters(self, detection_agent, app_selection, user_selection):
        """
        Optimiza los parámetros de detección para que app_selection sea más similar a user_selection.
        """
        best_similarity_score = -1  # Pearson correlation ranges from -1 to 1
        best_params = None

        for volume_sma_window in range(3, 10):
            for height_sma_window in range(3, 10):
                detected = detection_agent.detect(app_selection, volume_sma_window, height_sma_window)
                
                # Asegúrate de que user_selection y detected tengan la misma longitud
                common_index = user_selection.index.intersection(detected.index)
                user_selection_aligned = user_selection.loc[common_index].apply(pd.to_numeric, errors='coerce')
                detected_aligned = detected.loc[common_index].apply(pd.to_numeric, errors='coerce')

                # Verificar si hay datos comunes antes de calcular el coeficiente de correlación de Pearson
                if not user_selection_aligned.empty and not detected_aligned.empty:
                    # Asegúrate de que los datos sean del tipo numérico adecuado
                    user_selection_values = user_selection_aligned.values.flatten().astype(float)
                    detected_values = detected_aligned.values.flatten().astype(float)

                    # Calcular el coeficiente de correlación de Pearson como métrica de similitud
                    correlation, _ = pearsonr(user_selection_values, detected_values)
                    
                    # Imprimir los parámetros y la puntuación de similitud para depuración
                    print(f"volume_sma_window: {volume_sma_window}, height_sma_window: {height_sma_window}, correlation: {correlation}")

                    if correlation > best_similarity_score:
                        best_similarity_score = correlation
                        best_params = (volume_sma_window, height_sma_window)

                    self.db.save_adjustment_result('volume_sma_window', volume_sma_window, len(detected), len(user_selection), correlation)
                    self.db.save_adjustment_result('height_sma_window', height_sma_window, len(detected), len(user_selection), correlation)

        return best_params, best_similarity_score