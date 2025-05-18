import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

LIGAS_VALIDAS_IDS = [
    2, 3, 9, 11, 13, 16, 39, 40, 45, 61, 62, 71, 72, 73, 78, 79, 88, 94, 103, 106, 113,
    119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172, 179, 188,
    197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_fixtures():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json().get("response", [])
    return [f for f in data if f["league"]["id"] in LIGAS_VALIDAS_IDS]

def obtener_forma_y_estadisticas(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    r = requests.get(url, headers=HEADERS)
    return r.json().get("response", {}) if r.status_code == 200 else {}

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    r = requests.get(url, headers=HEADERS)
    data = r.json().get("response", [])
    cuotas = {}
    for item in data:
        for bookmaker in item.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                if bet["name"] == "Match Winner":
                    for val in bet.get("values", []):
                        cuotas[val["value"]] = val.get("odd")
                if bet["name"] == "Over/Under":
                    for val in bet.get("values", []):
                        if val["value"] == "Over 2.5":
                            cuotas["Over 2.5"] = val.get("odd")
                if bet["name"] == "Both Teams To Score":
                    for val in bet.get("values", []):
                        if val["value"] == "Yes":
                            cuotas["BTTS"] = val.get("odd")
    return cuotas

def analizar_partido(f):
    lid = f['league']['id']
    local = f['teams']['home']
    visitante = f['teams']['away']

    forma_local = obtener_forma_y_estadisticas(local['id'], lid)
    forma_visitante = obtener_forma_y_estadisticas(visitante['id'], lid)
    cuotas = obtener_cuotas(f["fixture"]["id"])

    goles_local = forma_local.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
    goles_visitante = forma_visitante.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
    goles_contra_local = forma_local.get("goals", {}).get("against", {}).get("average", {}).get("total", 0)
    goles_contra_visitante = forma_visitante.get("goals", {}).get("against", {}).get("average", {}).get("total", 0)

    prom_gf_local = float(goles_local or 0)
    prom_gf_visitante = float(goles_visitante or 0)
    marcador_local = round((prom_gf_local + goles_contra_visitante) / 2)
    marcador_visitante = round((prom_gf_visitante + goles_contra_local) / 2)

    marcador = f"{marcador_local} - {marcador_visitante}"
    total_goles = marcador_local + marcador_visitante

    recomendacion = ""
    if marcador_local > marcador_visitante:
        recomendacion = "Gana Local"
    elif marcador_visitante > marcador_local:
        recomendacion = "Gana Visitante"
    else:
        recomendacion = "Empate probable"

    mercados = []
    if total_goles >= 3:
        mercados.append("Over 2.5")
    elif total_goles <= 2:
        mercados.append("Under 2.5")
    if marcador_local > 0 and marcador_visitante > 0:
        mercados.append("BTTS (Ambos anotan)")

    print(f"\n{local['name']} vs {visitante['name']} ({f['league']['name']})")
    print(f"\U0001F4CA ML: {recomendacion} | BTTS: -- | Over 2.5: --")
    print(f"\U0001F4A1 Marcador tentativo: {marcador}")
    print(f"\U0001F4B8 Cuotas ML: Local {cuotas.get(local['name'], '-')}, Empate {cuotas.get('Draw', '-')}, Visitante {cuotas.get(visitante['name'], '-')} | Over 2.5: {cuotas.get('Over 2.5', '-')} | BTTS Sí: {cuotas.get('BTTS', '-')}\n")
    if recomendacion:
        print(f"\U0001F4C8 Recomendaciones: {recomendacion}, {', '.join(mercados)}")

def main():
    print(f"\n\U0001F4C5 Análisis de partidos del día {FECHA_HOY}")
    partidos = obtener_fixtures()
    print(f"\u2728 Total partidos encontrados: {len(partidos)}")
    for f in partidos:
        analizar_partido(f)

if __name__ == "__main__":
    main()
