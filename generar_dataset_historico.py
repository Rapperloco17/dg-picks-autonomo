# generar_dataset_historico.py

import pandas as pd
import os
import json

# Ruta donde están los archivos de resultados en Excel
EXCEL_DIR = "descargas"  # Cámbialo si están en otra carpeta

# Temporadas válidas para el histórico
TEMPORADAS_VALIDAS = [2022, 2023, 2024]

partidos = []

for filename in os.listdir(EXCEL_DIR):
    if filename.endswith(".xlsx") and filename.startswith("resultados_"):
        df = pd.read_excel(os.path.join(EXCEL_DIR, filename))

        if "temporada" not in df.columns:
            continue

        df_filtrado = df[df["temporada"].isin(TEMPORADAS_VALIDAS)].copy()
        df_filtrado["resultado"] = df_filtrado.apply(
            lambda row: "local" if row["goles_local"] > row["goles_visitante"]
            else "visitante" if row["goles_local"] < row["goles_visitante"]
            else "empate", axis=1
        )

        columnas = [
            "fixture_id", "fecha", "liga", "temporada",
            "equipo_local", "equipo_visitante",
            "goles_local", "goles_visitante", "resultado"
        ]

        partidos.extend(df_filtrado[columnas].to_dict(orient="records"))

# Guarda el histórico en JSON
output_path = "historial/historico_resultados_2022_2024.json"
os.makedirs("historial", exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print(f"✅ Histórico guardado en {output_path}")

