import os
import requests
import json
from datetime import datetime

# Configuración de API
API_KEY = os.getenv("API_FOOTBALL_KEY") or "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Ligas válidas (IDs y archivo de historial)
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

  

# ---------------------- FUNCIONES PRINCIPALES ----------------------

def obtener_fixtures_hoy():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get("response", [])
        return [f for f in fixtures if f['league']['id'] in LIGAS_VALIDAS]
    except:
        return []

def cargar_historial(liga_id):
    archivo = LIGAS_VALIDAS.get(liga_id)
    if not archivo:
        return []
    try:
        with open(f"historial/{archivo}", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def calcular_promedios(equipo, historial):
    partidos = [p for p in historial if p['equipo_local'] == equipo or p['equipo_visitante'] == equipo]
    if not partidos:
        return None
    goles_favor, goles_contra, tarjetas, corners = 0, 0, 0, 0
    for p in partidos:
        if p['equipo_local'] == equipo:
            goles_favor += p['goles_local']
            goles_contra += p['goles_visitante']
            tarjetas += p.get('amarillas_local', 0)
            corners += p.get('corners_local', 0)
        else:
            goles_favor += p['goles_visitante']
            goles_contra += p['goles_local']
            tarjetas += p.get('amarillas_visitante', 0)
            corners += p.get('corners_visitante', 0)
    n = len(partidos)
    return {
        "goles_favor": round(goles_favor / n, 2),
        "goles_contra": round(goles_contra / n, 2),
        "tarjetas": round(tarjetas / n, 2),
        "corners": round(corners / n, 2),
        "partidos": n
    }

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=1"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        apuestas = res.get("response", [])
        cuotas = {"ML": {}, "Over25": None, "BTTS": None}
        for ap in apuestas:
            for market in ap.get("bookmakers", []):
                for b in market.get("bets", []):
                    if b['name'] == "Match Winner":
                        for o in b['values']:
                            cuotas['ML'][o['value']] = o['odd']
                    elif b['name'] == "Over/Under":
                        for o in b['values']:
                            if o['value'] == "Over 2.5":
                                cuotas['Over25'] = o['odd']
                    elif b['name'] == "Both Teams To Score":
                        for o in b['values']:
                            if o['value'] == "Yes":
                                cuotas['BTTS'] = o['odd']
        return cuotas
    except:
        return {}

def sugerir_pick(casa, visita, cuotas):
    if not cuotas.get('ML'):
        return "Sin sugerencia"
    if casa['goles_favor'] > 1.5 and casa['goles_contra'] < 1.0:
        return f"Gana Local @ {cuotas['ML'].get('Home', '?')}"
    elif visita['goles_favor'] > 1.5 and visita['goles_contra'] < 1.0:
        return f"Gana Visitante @ {cuotas['ML'].get('Away', '?')}"
    elif casa['goles_favor'] + visita['goles_favor'] > 3.0:
        return f"Over 2.5 goles @ {cuotas.get('Over25', '?')}"
    elif casa['goles_favor'] > 1.2 and visita['goles_favor'] > 1.2:
        return f"Ambos Anotan @ {cuotas.get('BTTS', '?')}"
    else:
        return "Sin sugerencia"

def analizar_fixture(f):
    local = f['teams']['home']['name']
    visita = f['teams']['away']['name']
    lid = f['league']['id']
    fid = f['fixture']['id']
    historial = cargar_historial(lid)
    stats_local = calcular_promedios(local, historial)
    stats_visita = calcular_promedios(visita, historial)
    if not stats_local or not stats_visita:
        print(f"❌ Datos incompletos para {local} vs {visita}")
        return
    cuotas = obtener_cuotas(fid)
    pick = sugerir_pick(stats_local, stats_visita, cuotas)
    print(f"\n🔍 {local} vs {visita} — Liga: {f['league']['name']}")
    print(f"📊 Promedio Local: Goles: {stats_local['goles_favor']}, Tarjetas: {stats_local['tarjetas']}, Corners: {stats_local['corners']}")
    print(f"📊 Promedio Visitante: Goles: {stats_visita['goles_favor']}, Tarjetas: {stats_visita['tarjetas']}, Corners: {stats_visita['corners']}")
    print(f"✅ Pick sugerido: {pick}")

def main():
    print("\n⚽ Cargando fixtures del día...")
    fixtures = obtener_fixtures_hoy()
    print(f"✅ Se encontraron {len(fixtures)} partidos para analizar hoy.")
    for f in fixtures:
        analizar_fixture(f)

if __name__ == "__main__":
    main()
