import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY") or "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_VALIDAS = {
    1: "resultados_world_cup.json",
    2: "resultados_uefa_champions_league.json",
    3: "resultados_uefa_europa_league.json",
    4: "resultados_euro_championship.json",
    9: "resultados_copa_america.json",
    11: "resultados_conmebol_sudamericana.json",
    13: "resultados_conmebol_libertadores.json",
    16: "resultados_concacaf_champions_league.json",
    39: "resultados_premier_league.json",
    40: "resultados_championship.json",
    61: "resultados_ligue_1.json",
    62: "resultados_ligue_2.json",
    71: "resultados_serie_a.json",
    72: "resultados_serie_b.json",
    73: "resultados_copa_do_brasil.json",
    45: "resultados_fa_cup.json",
    78: "resultados_bundesliga.json",
    79: "resultados_2_bundesliga.json",
    88: "resultados_eredivisie.json",
    94: "resultados_primeira_liga.json",
    103: "resultados_eliteserien.json",
    106: "resultados_ekstraklasa.json",
    113: "resultados_allsvenskan.json",
    119: "resultados_superliga.json",
    128: "resultados_liga_profesional_argentina.json",
    129: "resultados_primera_nacional.json",
    130: "resultados_copa_argentina.json",
    135: "resultados_serie_a_italy.json",
    136: "resultados_serie_b_italy.json",
    137: "resultados_coppa_italia.json",
    140: "resultados_la_liga.json",
    141: "resultados_segunda_division.json",
    143: "resultados_copa_del_rey.json",
    144: "resultados_jupiler_pro_league.json",
    162: "resultados_primera_division_costa_rica.json",
    169: "resultados_super_league_china.json",
    188: "resultados_a_league.json",
    203: "resultados_super_lig.json",
    207: "resultados_super_league_switzerland.json",
    253: "resultados_major_league_soccer.json",
    262: "resultados_liga_mx.json",
    263: "resultados_liga_de_expansion_mx.json",
    265: "resultados_primera_division_chile.json",
    268: "resultados_primera_division_apertura.json",
    281: "resultados_primera_division_peru.json"
}

def obtener_fixtures_hoy():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        fixtures = response.json().get("response", [])
        print(f"\n✅ Se encontraron {len(fixtures)} partidos para analizar hoy.\n")
        return [f for f in fixtures if f['league']['id'] in LIGAS_VALIDAS]
    except requests.RequestException as e:
        print(f"\n❌ Error al obtener fixtures: {e}\n")
        return []

def obtener_estadisticas_y_cuotas(fixture_id):
    url_stats = f"{BASE_URL}/teams/statistics?fixture={fixture_id}"
    url_odds = f"{BASE_URL}/odds?fixture={fixture_id}"
    stats, odds = None, None

    try:
        res_stats = requests.get(url_stats, headers=HEADERS, timeout=10).json()
        res_odds = requests.get(url_odds, headers=HEADERS, timeout=10).json()

        stats = res_stats.get("response", {})
        odds_data = res_odds.get("response", [])

        if odds_data:
            odds = odds_data[0]["bookmakers"][0]["bets"]

        return stats, odds
    except Exception as e:
        print(f"❌ Error obteniendo detalles: {e}")
        return None, None

def analizar_fixture(fixture):
    local = fixture['teams']['home']['name']
    visitante = fixture['teams']['away']['name']
    lid = fixture['league']['id']
    nombre_liga = fixture['league']['name']
    fid = fixture['fixture']['id']

    stats, odds = obtener_estadisticas_y_cuotas(fid)
    if not stats or not odds:
        print(f"❌ Datos incompletos para fixture {fid}")
        return

    goles_local = stats.get("goals", {}).get("for", {}).get("average", {}).get("home")
    goles_visita = stats.get("goals", {}).get("for", {}).get("average", {}).get("away")
    corners = stats.get("corner", {}).get("total", 0)
    tarjetas = stats.get("cards", {}).get("yellow", {}).get("total", 0)

    pick = "No definido"
    cuota = "-"

    for bet in odds:
        if bet['name'] == "Match Winner":
            pick = f"Gana {local}"
            cuota = bet['values'][0]['odd']  # Local win
        elif bet['name'] == "Over/Under 2.5":
            pick = "Over 2.5 goles"
            cuota = bet['values'][0]['odd']
        elif bet['name'] == "Both Teams To Score":
            pick = "Ambos Anotan"
            cuota = bet['values'][0]['odd']
        break

    print(f"\n⚽ {local} vs {visitante}  — Liga: {nombre_liga} (Fixture ID: {fid})")
    print(f"📊 Promedios: Goles Local: {goles_local}, Goles Visita: {goles_visita}, Tarjetas: {tarjetas}, Corners: {corners}")
    print(f"💡 Pick sugerido: {pick} @ {cuota}")

def main():
    print("\n🚀 Cargando fixtures del día...")
    fixtures = obtener_fixtures_hoy()
    for f in fixtures:
        analizar_fixture(f)

if __name__ == "__main__":
    main()
