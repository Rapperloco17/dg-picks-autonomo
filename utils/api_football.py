import requests
import time

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

def obtener_partidos_de_liga(league_id, season):
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": season
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        print("Error al obtener partidos:", response.text)
        return []

def analizar_partido_futbol(partido):
    try:
        equipo_local = partido["teams"]["home"]["name"]
        equipo_visitante = partido["teams"]["away"]["name"]
        fecha = partido["fixture"]["date"]
        goles_local = partido["goals"]["home"]
        goles_visitante = partido["goals"]["away"]

        analisis = f"{equipo_local} vs {equipo_visitante} el {fecha}. Goles: {goles_local}-{goles_visitante}"
        return analisis
    except Exception as e:
        return f"Error al analizar partido: {e}"

if __name__ == "__main__":
    partidos = obtener_partidos_de_liga(39, 2024)  # Ejemplo: Premier League, temporada 2024
    for p in partidos[:5]:
        print(analizar_partido_futbol(p))
        time.sleep(1)
