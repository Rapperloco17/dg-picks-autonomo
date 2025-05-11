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
  "2": 2024, "3": 2024, "9": 2024, "16": 2024, "39": 2024, "45": 2024,
  "61": 2024, "62": 2024, "71": 2024, "78": 2024, "88": 2024, "94": 2024,
  "98": 2024, "106": 2024, "113": 2024, "118": 2024, "129": 2024, "130": 2024,
  "135": 2024, "140": 2024, "144": 2024, "195": 2024, "203": 2024, "210": 2024,
  "233": 2024, "239": 2024, "245": 2024, "253": 2024, "262": 2024, "271": 2024,
  "292": 2024, "1129": 2024, "1379": 2024, "1439": 2024
}

# === FUNCIONES ===
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

        goals_data = pred.get("predictions", {}).get("goals", {})
        goles_home_raw = goals_data.get("home")
        goles_away_raw = goals_data.get("away")
        goles_home = float(goles_home_raw) if goles_home_raw not in [None, '', '-', 'null'] else 0.0
        goles_away = float(goles_away_raw) if goles_away_raw not in [None, '', '-', 'null'] else 0.0
        total_goles_esperados = goles_home + goles_away
        print(f"\U0001F4A3 Goles esperados: {home} {goles_home} + {away} {goles_away} = {total_goles_esperados:.2f}")

        tendencia_goles = ""
        if total_goles_esperados >= 3.5:
            tendencia_goles = "Tendencia: Over 3.5"
        elif total_goles_esperados >= 2.5:
            tendencia_goles = "Tendencia: Over 2.5"
        elif total_goles_esperados >= 1.5:
            tendencia_goles = "Tendencia: Over 1.5"
        else:
            tendencia_goles = "Tendencia: Under 2.5"

        if goles_home >= 0.9 and goles_away >= 0.9:
            tendencia_goles += " | Probable BTTS ✅"
        print(tendencia_goles)

        # === CÓRNERS Y TARJETAS ===
        corners_home = corners_away = cards_home = cards_away = 0
        found_corners = found_cards = False

        for stat in stats:
            team = stat.get("team", {}).get("name", "").lower().strip()
            for s in stat.get("statistics", []):
                tipo = s.get("type", "").lower()
                val = s.get("value")
                if val is None: continue
                if "corner" in tipo:
                    found_corners = True
                    if home.lower() in team:
                        corners_home = val
                    elif away.lower() in team:
                        corners_away = val
                elif "yellow" in tipo or "red" in tipo:
                    found_cards = True
                    if home.lower() in team:
                        cards_home += val
                    elif away.lower() in team:
                        cards_away += val

        total_corners_avg = corners_home + corners_away
        total_cards_avg = cards_home + cards_away

        print(f"\n📊 CÓRNERS & TARJETAS – {home} vs {away}")
        if found_corners:
            print(f"Corners: {home} ({corners_home}) + {away} ({corners_away}) = Total {total_corners_avg}")
            if total_corners_avg >= 9:
                print("✅ PICK sugerido: Over 9.5 corners – Equipos con promedio alto")
        else:
            print("⚠️ No se encontraron datos de corners")

        if found_cards:
            print(f"Tarjetas: {home} ({cards_home}) + {away} ({cards_away}) = Total {total_cards_avg}")
            referee_info = fixture["fixture"].get("referee") or "Desconocido"
            referee_avg_cards = 4.8  # TODO: usar promedio real del árbitro si está disponible
            print(f"Árbitro: {referee_info} – Promedio de tarjetas: {referee_avg_cards}")
            if total_cards_avg >= 4.5:
                if referee_avg_cards >= 4.5:
                    print("✅ PICK sugerido: Over 4.5 tarjetas – Equipos y árbitro con tendencia alta")
                else:
                    print("✅ PICK sugerido: Over 4.5 tarjetas – Equipos con tendencia alta")
        else:
            print("⚠️ No se encontraron datos de tarjetas")

        # === CUOTAS ===
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

        # === PICK PRINCIPAL ===
        pick = None
        motivo = ""
        if cuota_ov25 and float(cuota_ov25) >= 1.70 and goles_home >= 1.2 and goles_away >= 1.2:
            pick = "Over 2.5 goles"
            motivo = "Promedio de goles alto"
        elif cuota_btts and float(cuota_btts) >= 1.70 and "w" in forma_local.lower() and "w" in forma_visitante.lower():
            pick = "Ambos anotan"
            motivo = "Buena forma y ataque de ambos"
        elif cuota_1x and float(cuota_1x) >= 1.50 and "w" in forma_local.lower():
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
