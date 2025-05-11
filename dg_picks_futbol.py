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

LIGAS_WHITELIST = {
  "2": 2024,
  "3": 2024,
  "9": 2024,
  "16": 2024,
  "39": 2024,
  "45": 2024,
  "61": 2024,
  "62": 2024,
  "71": 2024,
  "78": 2024,
  "88": 2024,
  "94": 2024,
  "98": 2024,
  "106": 2024,
  "113": 2024,
  "118": 2024,
  "129": 2024,
  "130": 2024,
  "135": 2024,
  "140": 2024,
  "144": 2024,
  "195": 2024,
  "203": 2024,
  "210": 2024,
  "233": 2024,
  "239": 2024,
  "245": 2024,
  "253": 2024,
  "262": 2024,
  "271": 2024,
  "292": 2024,
  "1129": 2024,
  "1379": 2024,
  "1439": 2024
}


# === FUNCIONES ===

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
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

        stats_team = pred.get("teams", {})
        forma_local = stats_team.get("home", {}).get("last_5", {}).get("form", "")
        forma_visitante = stats_team.get("away", {}).get("last_5", {}).get("form", "")
        print(f"\U0001F4CA Forma Local: {forma_local}")
        print(f"\U0001F4CA Forma Visitante: {forma_visitante}")

        promedio_goles = pred.get("comparisons", {}).get("goals", {})
        goles_home = promedio_goles.get("home", "0")
        goles_away = promedio_goles.get("away", "0")
        print(f"\U0001F4A3 Promedio de Goles: {goles_home} vs {goles_away}")

        markets = cuotas.get("bookmakers", [{}])[0].get("bets", [])
        cuota_ov25, cuota_btts, cuota_1x = None, None, None

        for market in markets:
            nombre = market.get("name", "").lower()
            if "over/under 2.5" in nombre:
                cuota_ov25 = market["values"][0]["odd"]
            if "both teams to score" in nombre:
                cuota_btts = market["values"][0]["odd"]
            if "double chance" in nombre:
                for val in market["values"]:
                    if val["value"] == "1X":
                        cuota_1x = val["odd"]

        print(f"\U0001F522 Cuota Over 2.5: {cuota_ov25}")
        print(f"\U0001F522 Cuota Ambos anotan: {cuota_btts}")
        print(f"\U0001F522 Cuota 1X: {cuota_1x}")

        pick = None
        motivo = ""
        if cuota_ov25 and float(cuota_ov25) >= 1.70 and float(goles_home) >= 1.2 and float(goles_away) >= 1.2:
            pick = "Over 2.5 goles"
            motivo = "Promedio de goles alto"
        elif cuota_btts and float(cuota_btts) >= 1.70 and "W" in forma_local and "W" in forma_visitante:
            pick = "Ambos anotan"
            motivo = "Buena forma y ataque de ambos"
        elif cuota_1x and float(cuota_1x) >= 1.50 and "W" in forma_local:
            pick = "1X (Local o empate)"
            motivo = "Local en buena forma"

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

# === PROCESO PRINCIPAL ===
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
