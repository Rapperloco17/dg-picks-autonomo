import requests
import json
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY") or "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

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

def sugerir_pick(stats_local, stats_visitante):
    gl, cl, btts_l, o25_l = stats_local.values()
    gv, cv, btts_v, o25_v = stats_visitante.values()

    if gl > gv and cl < cv:
        return "🟩 Gana Local"
    elif gv > gl and cv < cl:
        return "🟥 Gana Visitante"
    elif abs(gl - gv) < 0.3:
        return "🟨 Posible Empate"
    else:
        return "❓ Sin sugerencia"

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=6"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        markets = data.get("response", [])
        cuotas = {}
        for m in markets:
            for entry in m.get("bookmakers", []):
                for bet in entry.get("bets", []):
                    if bet['name'] == "Match Winner":
                        for odd in bet['values']:
                            cuotas[odd['value']] = odd['odd']
        return cuotas
    except:
        return {}

def analizar_fixture(f):
    lid = f['league']['id']
    lid_name = LIGAS_VALIDAS.get(lid, "Liga")
    fid = f['fixture']['id']
    local = f['teams']['home']['name']
    visitante = f['teams']['away']['name']

    # Datos simulados para ambos equipos (para pruebas)
    stats_local = {"gf": 1.6, "gc": 1.2, "btts": 58.3, "o25": 62.7}
    stats_visit = {"gf": 1.3, "gc": 1.4, "btts": 54.1, "o25": 51.3}
    pick = sugerir_pick(stats_local, stats_visit)
    cuotas = obtener_cuotas(fid)

    print(f"\n⚔️ {local} vs {visitante} (Fixture ID: {fid}, Liga: {lid_name})")
    print(f"📊 Stats Local: GF: {stats_local['gf']}, GC: {stats_local['gc']}, BTTS: {stats_local['btts']}%, Over 2.5: {stats_local['o25']}%")
    print(f"📊 Stats Visitante: GF: {stats_visit['gf']}, GC: {stats_visit['gc']}, BTTS: {stats_visit['btts']}%, Over 2.5: {stats_visit['o25']}%")
    if cuotas:
        print(f"🔢 Cuotas: Local {cuotas.get('Home', '-')}, Empate {cuotas.get('Draw', '-')}, Visitante {cuotas.get('Away', '-')}")
    print(f"🎯 Pick sugerido: {pick}")

def main():
    print("\n🚀 Obteniendo partidos válidos de hoy...")
    partidos = obtener_fixtures_hoy()
    for f in partidos:
        analizar_fixture(f)

if __name__ == "__main__":
    main()
