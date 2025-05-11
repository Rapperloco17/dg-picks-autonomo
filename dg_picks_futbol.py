
import requests
import json
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

LIGAS_WHITELIST = { "2": 2024, "3": 2024, "9": 2024, "16": 2024, "39": 2024, "45": 2024,
  "61": 2024, "62": 2024, "71": 2024, "78": 2024, "88": 2024, "94": 2024,
  "98": 2024, "106": 2024, "113": 2024, "118": 2024, "129": 2024, "130": 2024,
  "135": 2024, "140": 2024, "144": 2024, "195": 2024, "203": 2024, "210": 2024,
  "233": 2024, "239": 2024, "245": 2024, "253": 2024, "262": 2024, "271": 2024,
  "292": 2024, "1129": 2024, "1379": 2024, "1439": 2024 }

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}&status=NS"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", [])

def obtener_prediccion(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS).json()
    return res.get("response", [{}])[0]

def obtener_estadisticas_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    res = requests.get(url, headers=HEADERS).json()
    return res.get("response", {})

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS).json()
    data = res.get("response", [])
    if not data:
        print("❌ No hay cuotas disponibles para este partido.")
        return {}
    return data[0]

def analizar_fixture(fixture):
    fixture_id = fixture["fixture"]["id"]
    liga_id = str(fixture["league"]["id"])
    if liga_id not in LIGAS_WHITELIST:
        return

    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]
    home_id = home["id"]
    away_id = away["id"]
    home_name = home["name"]
    away_name = away["name"]
    print(f"\n📅 {home_name} vs {away_name} (Liga {liga_id})")

    pred = obtener_prediccion(fixture_id)
    stats_home = obtener_estadisticas_equipo(home_id, liga_id)
    stats_away = obtener_estadisticas_equipo(away_id, liga_id)
    cuotas = obtener_cuotas(fixture_id)

    goles_home = stats_home.get("goals", {}).get("average", {}).get("home")
    goles_away = stats_away.get("goals", {}).get("average", {}).get("away")
    try:
        gh = float(goles_home or 0)
        ga = float(goles_away or 0)
    except:
        gh, ga = 0, 0

    # Predicción de marcador
    marcador = pred.get("predictions", {}).get("score", {}).get("fulltime", {})
    g1 = marcador.get("home")
    g2 = marcador.get("away")
    winner = pred.get("predictions", {}).get("winner", {}).get("name")

    if g1 is not None and g2 is not None and (g1, g2) != (0, 0):
        print(f"🧠 Marcador estimado (API): {home_name} {g1} - {g2} {away_name}")
    elif winner and winner.lower() != "draw":
        est_home = round(gh * 1.1)
        est_away = round(ga * 1.0)
        print(f"🧠 Marcador estimado (DG Picks): {home_name} {est_home} - {est_away} {away_name}")
    else:
        print("🧠 Marcador estimado: No disponible")

    print(f"📊 Predicción de ganador: {winner if winner else 'Empate probable'}")

    print("🔍 Estadísticas comparadas:")
    print(f"➡️ Goles promedio: {home_name} (local) {goles_home or 'N/D'} | {away_name} (visita) {goles_away or 'N/D'}")
    tiros_home = stats_home.get("shots", {})
    tiros_away = stats_away.get("shots", {})
    print(f"🎯 Tiros: {home_name} {tiros_home if tiros_home else 'N/D'} | {away_name} {tiros_away if tiros_away else 'N/D'}")
    posesion_home = stats_home.get("biggest", {}).get("ball_possession") or "N/D"
    posesion_away = stats_away.get("biggest", {}).get("ball_possession") or "N/D"
    print(f"📈 Posesión estimada: {home_name}: {posesion_home} | {away_name}: {posesion_away}")

    # Cuotas
    markets = cuotas.get("bookmakers", [{}])[0].get("bets", [])
    cuota_over25 = cuota_btts = cuota_1x = None
    for m in markets:
        name = m.get("name", "").lower()
        if "over/under 2.5" in name:
            cuota_over25 = m["values"][0]["odd"]
        if "both teams to score" in name:
            cuota_btts = m["values"][0]["odd"]
        if "double chance" in name:
            for val in m["values"]:
                if val["value"] == "1X":
                    cuota_1x = val["odd"]

    print(f"💸 Cuotas: Over 2.5: {cuota_over25} | BTTS: {cuota_btts} | 1X: {cuota_1x}")

    # Pick sugerido
    if cuota_over25 and gh >= 1.2 and ga >= 1.2:
        try:
            if float(cuota_over25) >= 1.70:
                print(f"✅ PICK: Over 2.5 goles @ {cuota_over25} – Promedio alto de goles detectado")
        except:
            pass

def main():
    print("🔎 Analizando partidos de hoy...")
    for fixture in obtener_fixtures_hoy():
        analizar_fixture(fixture)

if __name__ == "__main__":
    main()
