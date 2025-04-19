# utils/api_football.py (actualizado con lectura de JSON y todas las ligas permitidas)

import requests
import json
from datetime import datetime

API_URL = "https://v3.football.api-sports.io"
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"  # API Key válida del usuario

headers = {
    "x-apisports-key": API_KEY
}

# Leer ligas válidas desde JSON externo
with open("utils/leagues_whitelist_ids.json") as f:
    ligas_validas = json.load(f)

# Leer temporadas correctas por liga desde JSON
with open("utils/league_seasons.json") as f:
    temporadas_por_liga = json.load(f)

# Fecha actual en formato YYYY-MM-DD
fecha_hoy = datetime.now().strftime("%Y-%m-%d")


def obtener_partidos_de_liga(liga_id, fecha):
    temporada = temporadas_por_liga.get(str(liga_id), 2025)  # ← Usa 2025 por defecto si no está
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha
    }
    try:
        response = requests.get(f"{API_URL}/fixtures", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\u26a0\ufe0f Error al conectar con la API para liga {liga_id}:", e)
        return {"response": []}


# Ejemplo de ejecución para testeo directo
if __name__ == "__main__":
    resultados = {}
    for liga_id, liga_nombre in ligas_validas.items():
        data = obtener_partidos_de_liga(int(liga_id), fecha_hoy)
        resultados[liga_nombre] = len(data.get("response", []))

    print("\nResumen de partidos encontrados hoy:")
    for liga, cantidad in resultados.items():
        print(f"- {liga}: {cantidad} partidos")

