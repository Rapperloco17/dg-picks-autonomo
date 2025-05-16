import pandas as pd
import os
import json

# Ruta al Excel y a los historiales
ligas_path = "ligas_activas.xlsx"
historial_folder = "historial/unificados"

# Cargar ligas activas
df_ligas = pd.read_excel(ligas_path)
ligas_activas_ids = df_ligas[df_ligas['Activa'] == True]['League ID'].tolist()

# Diccionario para guardar los historiales por ID
historico_por_liga = {}

for league_id in ligas_activas_ids:
    archivo = f"resultados_{league_id}.json"
    ruta_json = os.path.join(historial_folder, archivo)

    if os.path.exists(ruta_json):
        with open(ruta_json, "r", encoding="utf-8") as f:
            historico_por_liga[league_id] = json.load(f)
    else:
        print(f"\u26a0\ufe0f No se encontr\u00f3 el archivo: {archivo}")

# Ahora ya puedes usar historico_por_liga[league_id] para análisis

