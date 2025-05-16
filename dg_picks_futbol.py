# dg_picks_futbol.py — Carga de historiales integrados
import os
import json

# Lista exacta de League IDs desde 'lista definitiva.xlsx'
ligas_activas_ids = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88,
    94, 103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143,
    144, 162, 164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242,
    244, 253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

# Ruta a la carpeta de historiales unificados
historial_folder = "historial/unificados"

# Diccionario donde se cargan los historiales por liga
historico_por_liga = {}

for league_id in ligas_activas_ids:
    archivo = f"resultados_{league_id}.json"
    ruta_json = os.path.join(historial_folder, archivo)

    if os.path.exists(ruta_json):
        with open(ruta_json, "r", encoding="utf-8") as f:
            historico_por_liga[league_id] = json.load(f)
    else:
        print(f"⚠️ Archivo no encontrado: {archivo}")

# 🔹 Este bloque ya está dentro de dg_picks_futbol.py y listo para usarse en el análisis diario
