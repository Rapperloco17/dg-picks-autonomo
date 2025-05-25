
import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94, 103,
    106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164, 169,
    172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262, 263, 265,
    268, 271, 281, 345, 357
]

def float_safe(valor):
    try:
        return float(valor)
    except:
        return 0.0

def obtener_partidos_de_hoy():
    hoy = datetime.now().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    partidos = data.get("response", [])
    return [p for p in partidos if p["league"]["id"] in LIGAS_VALIDAS]

def obtener_stats_equipo(team_id, league_id, season):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", {})

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=1"
    response = requests.get(url, headers=HEADERS)
    data = response.json().get("response", [])
    if not data:
        return {}
    try:
        odds = data[0]["bookmakers"][0]["bets"]
        cuotas = {}
        for mercado in odds:
            if mercado["name"] == "Match Winner":
                for o in mercado["values"]:
                    cuotas[o["value"]] = float_safe(o["odd"])
        return cuotas
    except Exception:
        return {}

def imprimir_analisis(p):
    home = p["teams"]["home"]
    away = p["teams"]["away"]
    fixture = p["fixture"]
    league = p["league"]
    season = league["season"]

    stats_home = obtener_stats_equipo(home["id"], league["id"], season)
    stats_away = obtener_stats_equipo(away["id"], league["id"], season)
    cuotas = obtener_cuotas(fixture["id"])

    if not stats_home or not stats_away:
        return

    gf_home = float_safe(stats_home.get("goals", {}).get("for", {}).get("average", {}).get("home", 0))
    ga_home = float_safe(stats_home.get("goals", {}).get("against", {}).get("average", {}).get("home", 0))
    gf_away = float_safe(stats_away.get("goals", {}).get("for", {}).get("average", {}).get("away", 0))
    ga_away = float_safe(stats_away.get("goals", {}).get("against", {}).get("average", {}).get("away", 0))

    form_home = stats_home.get("form", "")[-5:]
    form_away = stats_away.get("form", "")[-5:]
    wins_home = form_home.count("W")
    wins_away = form_away.count("W")

    cuota_home = float_safe(cuotas.get("Home", 0))
    cuota_away = float_safe(cuotas.get("Away", 0))
    cuota_draw = float_safe(cuotas.get("Draw", 0))

    goles_esperados_home = round((gf_home + ga_away) / 2, 2)
    goles_esperados_away = round((gf_away + ga_home) / 2, 2)
    goles_totales = goles_esperados_home + goles_esperados_away

    prob_btts = "Alta (80%)" if goles_esperados_home >= 1.0 and goles_esperados_away >= 1.0 else "Baja (40%)"
    prob_over25 = "Probable (70%)" if goles_totales >= 2.5 else "Poco probable (30%)"

    print(f"🔍 PARTIDO: {home['name']} vs {away['name']}")
    print(f"Liga: {league['name']} | Fecha: {fixture['date']}")
    print(f"📊 Forma reciente: {home['name']}: {form_home} | {away['name']}: {form_away}")
    print(f"🏟️ Goles Local: {gf_home} GF / {ga_home} GC | Goles Visitante: {gf_away} GF / {ga_away} GC")
    print(f"🎯 Marcador estimado: {goles_esperados_home} – {goles_esperados_away}")
    print(f"📈 Probabilidad estimada: BTTS: {prob_btts} | Over 2.5 goles: {prob_over25}")
    print("💸 Cuotas:")
    print(f"1: {cuota_home}, X: {cuota_draw}, 2: {cuota_away}")

    pick = None
    justificacion = ""

    if wins_home >= 3 and gf_home >= 1.6 and ga_away >= 1.5 and cuota_home >= 1.60:
        pick = f"{home['name']} ML @ {cuota_home}"
        justificacion = "Local fuerte en casa, visitante concede mucho."
    elif wins_away >= 3 and gf_away >= 1.5 and ga_home >= 1.5 and cuota_away >= 2.20:
        pick = f"{away['name']} ML @ {cuota_away}"
        justificacion = "Visitante en buena forma y local débil."
    elif form_home.count("D") >= 2 and form_away.count("D") >= 2 and cuota_draw >= 3.00:
        pick = f"Empate @ {cuota_draw}"
        justificacion = "Ambos empatan con frecuencia y marcan poco."

    if pick:
        print(f"✅ PICK RECOMENDADO: {pick}")
        print(f"📌 Justificación: {justificacion}")
    else:
        print("❌ No se recomienda pick para este partido.\n")

def main():
    partidos = obtener_partidos_de_hoy()
    print(f"Total de partidos válidos hoy: {len(partidos)}\n")
    for p in partidos:
        imprimir_analisis(p)
        print("-" * 80)

if __name__ == "__main__":
    main()
