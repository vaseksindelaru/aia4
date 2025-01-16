import pandas as pd
from streamlit_app.db.database import Database
from sklearn.metrics import mean_squared_error

class AdjustAgent:
    def __init__(self, db_user, db_password, db_host, db_database):
        self.db = Database(db_user, db_password, db_host, db_database, "adjustment_results")

    def optimize_parameters(self, detection_agent, app_selection, user_selection):
        """
        Optimiza los parámetros de detección para que app_selection sea más similar a user_selection.
        """
        best_similarity_score = float('inf')
        best_params = None

        for volume_sma_window in range(3, 10):
            for height_sma_window in range(3, 10):
                detected = detection_agent.detect(app_selection, volume_sma_window, height_sma_window)
                
                # Asegúrate de que user_selection y detected tengan la misma longitud
                common_index = user_selection.index.intersection(detected.index)
                user_selection_aligned = user_selection.loc[common_index]
                detected_aligned = detected.loc[common_index]

                # Calcular el error cuadrático medio (MSE) como métrica de similitud
                similarity_score = mean_squared_error(user_selection_aligned, detected_aligned)
                
                if similarity_score < best_similarity_score:
                    best_similarity_score = similarity_score
                    best_params = (volume_sma_window, height_sma_window)

                self.db.save_adjustment_result('volume_sma_window', volume_sma_window, len(detected), len(user_selection), similarity_score)
                self.db.save_adjustment_result('height_sma_window', height_sma_window, len(detected), len(user_selection), similarity_score)

        return best_params, best_similarity_score