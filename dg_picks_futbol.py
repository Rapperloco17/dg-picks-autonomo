import requests
import os
import json
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY") or "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Lista de ligas válidas (solo IDs)
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
    141: "resultados_segunda_división.json",
    143: "resultados_copa_del_rey.json",
    144: "resultados_jupiler_pro_league.json",
    162: "resultados_primera_división_costa_rica.json",
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
    263: "resultados_liga_de_expansión_mx.json",
    265: "resultados_primera_división_chile.json",
    268: "resultados_primera_división_apertura.json",
    271: "resultados_nb_i.json",
    281: "resultados_primera_división_peru.json",
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
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json().get("response", [])
        if len(data) < 2:
            return None, None
        return data[0], data[1]
    except:
        return None, None

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=1"
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        markets = res.json().get("response", [])
        cuotas = {
            "ML": {},
            "Over2.5": None,
            "BTTS": None
        }
        for market in markets:
            if market['bet']['name'] == 'Match Winner':
                for val in market['values']:
                    cuotas['ML'][val['value']] = val['odd']
            if market['bet']['name'] == 'Over/Under 2.5 goals':
                for val in market['values']:
                    if val['value'] == "Over 2.5":
                        cuotas['Over2.5'] = val['odd']
            if market['bet']['name'] == 'Both Teams To Score':
                for val in market['values']:
                    if val['value'] == "Yes":
                        cuotas['BTTS'] = val['odd']
        return cuotas
    except:
        return None

def imprimir_analisis(fixture):
    local = fixture['teams']['home']['name']
    visitante = fixture['teams']['away']['name']
    liga = fixture['league']['name']
    fid = fixture['fixture']['id']
    print(f"\n\U0001F4CA Análisis para Fixture ID: {fid} — {local} vs {visitante}, Liga: {liga}")

    stats_local, stats_visita = obtener_detalles_fixture(fid)
    if not stats_local or not stats_visita:
        print(f"❌ Datos incompletos para fixture {fid}")
        return

    def parse_stats(stats):
        s = {x['type']: x['value'] for x in stats.get('statistics', []) if x['value'] is not None}
        return {
            "goles": s.get('Goals', 0),
            "posesion": s.get('Ball Possession', 0),
            "amarillas": s.get('Yellow Cards', 0),
            "rojas": s.get('Red Cards', 0),
            "corners": s.get('Corner Kicks', 0),
            "faltas": s.get('Fouls', 0)
        }

    s_local = parse_stats(stats_local)
    s_visita = parse_stats(stats_visita)

    print(f"\n\U0001F3E0 Stats de {local}:")
    for k, v in s_local.items():
        print(f"{k.title()}: {v}")
    print(f"\n\U0001F3E2 Stats de {visitante}:")
    for k, v in s_visita.items():
        print(f"{k.title()}: {v}")

    cuotas = obtener_cuotas(fid)
    if cuotas:
        print("\n\U0001F4B0 Cuotas:")
        if cuotas['ML']:
            print(f"Ganador Local: {cuotas['ML'].get(local)} | Empate: {cuotas['ML'].get('Draw')} | Visitante: {cuotas['ML'].get(visitante)}")
        print(f"Over 2.5: {cuotas['Over2.5']} | BTTS: {cuotas['BTTS']}")
    else:
        print("\n⚠️ Cuotas no disponibles para este fixture.")

def main():
    print("\n🚀 Cargando fixtures del día...")
    fixtures = obtener_fixtures_hoy()
    for f in fixtures[:10]:  # Limitar análisis por ahora
        imprimir_analisis(f)

if __name__ == "__main__":
    main()
