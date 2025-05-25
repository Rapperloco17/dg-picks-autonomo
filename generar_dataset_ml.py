
import os
import json
import pandas as pd

# Carpeta donde están los archivos históricos
CARPETA = "historial"
archivos = [f for f in os.listdir(CARPETA) if f.startswith("resultados_") and f.endswith(".json")]

data_final = []

for archivo in archivos:
    with open(os.path.join(CARPETA, archivo), "r", encoding="utf-8") as f:
        data = json.load(f)

    for partido in data:
        try:
            local = partido["equipo_local"]
            visitante = partido["equipo_visitante"]
            goles_local = int(partido["goles_local"])
            goles_visitante = int(partido["goles_visitante"])
            fecha = partido.get("fecha", "")
            liga = partido.get("liga", "")

            over_2_5 = 1 if goles_local + goles_visitante > 2.5 else 0
            btts = 1 if goles_local > 0 and goles_visitante > 0 else 0

            data_final.append({
                "fecha": fecha,
                "liga": liga,
                "equipo_local": local,
                "equipo_visitante": visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "over_2_5": over_2_5,
                "btts": btts
            })

        except Exception as e:
            print(f"Error en {archivo}: {e}")

# Guardamos solo el JSON para evitar uso de openpyxl
with open("dataset_ml_base.json", "w", encoding="utf-8") as f_json:
    json.dump(data_final, f_json, indent=4, ensure_ascii=False)

print("✅ Dataset generado correctamente en dataset_ml_base.json")
