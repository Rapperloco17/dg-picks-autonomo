# Módulo principal para analizar partidos de fútbol

import requests
import os
from datetime import datetime

API_URL = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

# Lista de ligas válidas (IDs autorizados por el usuario)
LIGAS_VALIDAS = [
    2, 3, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94, 103, 106, 113,
    119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172,
    179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262, 263, 265,
    268, 271, 281, 345, 357
]

# Obtener partidos del día actual (fixtures por fecha)
def obtener_partidos_hoy():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    url = f"{API_URL}/fixtures?date={fecha_actual}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if data.get("response"):
        return [p for p in data["response"] if p["league"]["id"] in LIGAS_VALIDAS]
    return []

# Punto de entrada del análisis
def main():
    print("⚽ Análisis de partidos del día", datetime.now().strftime("%Y-%m-%d"))
    partidos = obtener_partidos_hoy()
    print("📌 Total partidos encontrados:", len(partidos))

if __name__ == "__main__":
    main()
