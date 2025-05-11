# Archivo unificado: dg_picks_futbol.py

import requests
import json
from datetime import datetime

# === CONFIGURACION ===
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
    data = response.json()
    return data.get("response", [])

def obtener_prediccion_fixture(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [{}])[0]

def obtener_estadisticas_fixture(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [])

def obtener_cuotas_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [{}])[0]

def analizar_fixture(fixture):
    fixture_id = fixture["fixture"]["id"]
    liga_id = str(fixture["league"]["id"])
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    print(f"\n\U0001F4C5 Partido: {home} vs {away} (Liga {liga_id})")

    if liga_id not in LIGAS_WHITELIST:
        print("\u274C Liga no permitida.")
        return None

    try:
        pred = obtener_prediccion_fixture(fixture_id)
        stats = obtener_estadisticas_fixture(fixture_id)
        cuotas = obtener_cuotas_fixture(fixture_id)

        pred_api = pred.get("predictions", {}).get("winner", {}).get("name", "?")
        print(f"\u2728 Predicción API: {pred_api}")

        marcador = pred.get("predictions", {}).get("score", {}).get("fulltime", {})
        g_home = marcador.get("home")
        g_away = marcador.get("away")
        if g_home is not None and g_away is not None:
            print(f"📊 Marcador predicho: {home} {g_home} – {g_away} {away}")

        goals_data = pred.get("predictions", {}).get("goals", {})
        goles_home = float(goals_data.get("home", 0) or 0)
        goles_away = float(goals_data.get("away", 0) or 0)
        if goles_home < 0: goles_home = 0
        if goles_away < 0: goles_away = 0
        total_goles = goles_home + goles_away
        print(f"\U0001F4A3 Goles esperados: {home} {goles_home} + {away} {goles_away} = {total_goles:.2f}")

        if total_goles >= 3.5:
            print("Tendencia: Over 3.5")
        elif total_goles >= 2.5:
            print("Tendencia: Over 2.5")
        elif total_goles >= 1.5:
            print("Tendencia: Over 1.5")
        else:
            print("Tendencia: Under 2.5")

        if goles_home >= 0.9 and goles_away >= 0.9:
            print("Probable BTTS ✅")

        corners_home = corners_away = cards_home = cards_away = 0
        for stat in stats:
            team_id = stat.get("team", {}).get("id")
            for s in stat.get("statistics", []):
                tipo = s.get("type", "").lower()
                val = s.get("value")
                if val is None: continue
                if "corner" in tipo:
                    if team_id == home_id:
                        corners_home = val
                    elif team_id == away_id:
                        corners_away = val
                elif "yellow" in tipo or "red" in tipo:
                    if team_id == home_id:
                        cards_home += val
                    elif team_id == away_id:
                        cards_away += val

        print(f"\n📊 CÓRNERS & TARJETAS – {home} vs {away}")
        print(f"Corners promedio: {home} ({corners_home}) | {away} ({corners_away}) | Total: {corners_home + corners_away}")
        print(f"Tarjetas promedio: {home} ({cards_home}) | {away} ({cards_away}) | Total: {cards_home + cards_away}")

        referee = fixture["fixture"].get("referee", "Desconocido")
        referee_avg = 4.8  # placeholder real si lo deseas
        print(f"Árbitro: {referee} – Promedio estimado: {referee_avg}")

        if corners_home + corners_away >= 9:
            print("✅ PICK sugerido: Over 9.5 corners")
        if cards_home + cards_away >= 4.5:
            print("✅ PICK sugerido: Over 4.5 tarjetas")

        markets = cuotas.get("bookmakers", [{}])[0].get("bets", [])
        cuota_ov25 = cuota_btts = cuota_1x = None
        for market in markets:
            name = market.get("name", "").lower()
            if "over/under 2.5" in name:
                cuota_ov25 = market["values"][0]["odd"]
            if "both teams to score" in name:
                cuota_btts = market["values"][0]["odd"]
            if "double chance" in name:
                for val in market["values"]:
                    if val["value"] == "1X":
                        cuota_1x = val["odd"]

        print(f"\U0001F522 Cuota Over 2.5: {cuota_ov25}")
        print(f"\U0001F522 Cuota Ambos anotan: {cuota_btts}")
        print(f"\U0001F522 Cuota 1X: {cuota_1x}")

        pick = motivo = None
        if cuota_ov25 and float(cuota_ov25) >= 1.70 and goles_home >= 1.2 and goles_away >= 1.2:
            pick = "Over 2.5 goles"
            motivo = "Promedio de goles alto"
        elif cuota_btts and float(cuota_btts) >= 1.70 and goles_home >= 1.0 and goles_away >= 1.0:
            pick = "Ambos anotan"
            motivo = "Ambos con gol esperado alto"
        elif cuota_1x and float(cuota_1x) >= 1.50:
            pick = "1X (Local o empate)"
            motivo = "Local con buen respaldo"

        if pick:
            print(f"\u2705 PICK: {pick} | Motivo: {motivo}")
            return {
                "partido": f"{home} vs {away}",
                "pick": pick,
                "cuota": cuota_ov25 or cuota_btts or cuota_1x,
                "motivo": motivo,
                "fecha_generacion": datetime.now().isoformat()
            }
        else:
            print("\u274C No se generó pick con valor.")
            return None

    except Exception as e:
        print(f"\u274C Error en fixture {fixture_id}: {e}")
        return None

def main():
    print("\U0001F50D Buscando partidos del día...")
    fixtures = obtener_fixtures_hoy()
    picks = []
    for fixture in fixtures:
        pick = analizar_fixture(fixture)
        if pick:
            picks.append(pick)
    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=4)
    print("\n\U0001F3AF Análisis finalizado. Picks guardados en output/picks_futbol.json")

if __name__ == "__main__":
    main()
