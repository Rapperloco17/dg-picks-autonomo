import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

# Lista oficial de ligas válidas para análisis
LIGAS_VALIDAS_IDS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144,
    162, 164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244,
    253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_fixtures_del_dia():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    partidos = []

    for item in data.get("response", []):
        liga_id = item["league"]["id"]
        if liga_id not in LIGAS_VALIDAS_IDS:
            continue
        partidos.append({
            "fixture_id": item["fixture"]["id"],
            "liga": item["league"]["name"],
            "local": item["teams"]["home"]["name"],
            "visitante": item["teams"]["away"]["name"],
            "local_id": item["teams"]["home"]["id"],
            "visitante_id": item["teams"]["away"]["id"]
        })
    return partidos

def obtener_forma_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&season=2024&league={league_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    return response.json().get("response", {})

def analizar_partido(partido):
    forma_local = obtener_forma_equipo(partido["local_id"], partido["fixture_id"])
    forma_visitante = obtener_forma_equipo(partido["visitante_id"], partido["fixture_id"])

    if not forma_local or not forma_visitante:
        print(f"⚠️ Datos incompletos: {partido['local']} vs {partido['visitante']}")
        return

    try:
        gf_local = float(forma_local.get("goals", {}).get("for", {}).get("average", {}).get("home", 0))
        gf_visitante = float(forma_visitante.get("goals", {}).get("for", {}).get("average", {}).get("away", 0))
        marcador_tentativo = f"{gf_local:.1f} - {gf_visitante:.1f}"
        print(f"\n📊 {partido['local']} vs {partido['visitante']} ({partido['liga']})")
        print(f"🧠 ML: -- | BTTS: -- | Over 2.5: --")
        print(f"🔮 Marcador tentativo: {marcador_tentativo}")
    except Exception as e:
        print(f"❌ Error en análisis: {partido['local']} vs {partido['visitante']} → {str(e)}")

def main():
    print(f"\n🧠 Análisis de partidos del día {FECHA_HOY}")
    partidos = obtener_fixtures_del_dia()
    print(f"📌 Total partidos encontrados: {len(partidos)}")
    for partido in partidos:
        analizar_partido(partido)

if __name__ == "__main__":
    main()
