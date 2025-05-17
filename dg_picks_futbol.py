import requests
import json
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
    164: "resultados_urvalsdeild.json",
    169: "resultados_super_league_china.json",
    172: "resultados_first_league.json",
    179: "resultados_premiership.json",
    188: "resultados_a_league.json",
    197: "resultados_super_league_1.json",
    203: "resultados_super_lig.json",
    207: "resultados_super_league_switzerland.json",
    210: "resultados_hnl.json",
    218: "resultados_bundesliga_austria.json",
    239: "resultados_primera_a.json",
    242: "resultados_liga_pro.json",
    244: "resultados_veikkausliiga.json",
    253: "resultados_major_league_soccer.json",
    257: "resultados_us_open_cup.json",
    262: "resultados_liga_mx.json",
    263: "resultados_liga_de_expansion_mx.json",
    265: "resultados_primera_division_chile.json",
    268: "resultados_primera_division_apertura.json",
    271: "resultados_nb_i.json",
    281: "resultados_primera_division_peru.json",
    345: "resultados_czech_liga.json",
    357: "resultados_premier_division_ireland.json"
}

def obtener_fixtures_hoy():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        fixtures = data.get("response", [])
        print(f"\n✅ Se encontraron {len(fixtures)} partidos para analizar hoy.\n")
        return [f for f in fixtures if f['league']['id'] in LIGAS_VALIDAS]
    except requests.RequestException as e:
        print(f"\n❌ Error al obtener partidos: {e}\n")
        return []

def obtener_detalles_fixture(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json().get("response", [])
        if not data or len(data) < 2:
            print(f"❌ Datos incompletos para fixture {fixture_id}")
            return None
        return data
    except Exception as e:
        print(f"❌ Error al obtener detalles para {fixture_id}: {e}")
        return None

def main():
    print("\n🚀 Cargando fixtures del día...")
    fixtures = obtener_fixtures_hoy()
    for fixture in fixtures:
        fixture_id = fixture['fixture']['id']
        print(f"\n⚽ Análisis para Fixture ID: {fixture_id}")
        detalles = obtener_detalles_fixture(fixture_id)
        if detalles:
            print("✅ Datos recibidos, procesando...")

if __name__ == "__main__":
    main()
