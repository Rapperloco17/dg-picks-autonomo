# utils/api_football.py (con ajustes completos)

import requests
from datetime import datetime

API_URL = "https://v3.football.api-sports.io"
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"  # ← Tu clave real activa

headers = {
    "x-apisports-key": API_KEY
}

# Ligas permitidas con IDs reales desde leagues_whitelist_ids.json
ligas_validas = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    253: "Championship",
    262: "Liga MX",
    71: "Eredivisie",
    94: "Primeira Liga",
    203: "Brasileirao",
    129: "MLS",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "Conference League",
    667: "Copa Libertadores",
    307: "Argentina Liga Profesional",
    301: "Copa Sudamericana",
    63: "Bélgica First Division A",
    36: "Turquía Super Lig",
    6334: "Championship (alt ID)"
}

# Fecha actual en formato YYYY-MM-DD
fecha_hoy = datetime.now().strftime("%Y-%m-%d")


def obtener_partidos_de_liga(liga_id, fecha):
    params = {
        "league": liga_id,
        "season": 2025,
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
    for liga_id in ligas_validas:
        data = obtener_partidos_de_liga(liga_id, fecha_hoy)
        resultados[ligas_validas[liga_id]] = len(data.get("response", []))

    print("\nResumen de partidos encontrados hoy:")
    for liga, cantidad in resultados.items():
        print(f"- {liga}: {cantidad} partidos")
