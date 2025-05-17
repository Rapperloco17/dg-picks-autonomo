import os
import requests
import json
from datetime import datetime

# Cargar API Key desde entorno Railway
API_KEY = os.getenv("API_FOOTBALL_KEY")

# Diccionario de ligas con ID y nombre de archivo json
LEAGUE_ID_TO_FILENAME = {
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

def obtener_partidos_hoy(api_key, league_ids):
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": api_key}

    partidos = []
    for league_id in league_ids:
        params = {"league": league_id, "season": 2024, "date": hoy}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get("response"):
            partidos.extend(data["response"])

    return partidos

def calcular_stats(equipo, partidos):
    goles_favor = []
    goles_contra = []
    btts = []
    over25 = []

    for p in partidos:
        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")
        goles_local = p.get("goles_local")
        goles_visitante = p.get("goles_visitante")

        if local is None or visitante is None or goles_local is None or goles_visitante is None:
            continue

        if equipo == local or equipo == visitante:
            if equipo == local:
                gf = goles_local
                gc = goles_visitante
            else:
                gf = goles_visitante
                gc = goles_local

            goles_favor.append(gf)
            goles_contra.append(gc)
            btts.append(1 if goles_local > 0 and goles_visitante > 0 else 0)
            over25.append(1 if goles_local + goles_visitante > 2.5 else 0)

    total = len(goles_favor)
    if total == 0:
        return {"juegos": 0, "goles_favor": 0, "goles_contra": 0, "btts_pct": 0, "over25_pct": 0}

    return {
        "juegos": total,
        "goles_favor": sum(goles_favor) / total,
        "goles_contra": sum(goles_contra) / total,
        "btts_pct": 100 * sum(btts) / total,
        "over25_pct": 100 * sum(over25) / total
    }

if __name__ == "__main__":
    print("📊 Obteniendo partidos válidos de hoy...")
    fixtures = obtener_partidos_hoy(API_KEY, LEAGUE_ID_TO_FILENAME.keys())
    print(f"🔎 Se encontraron {len(fixtures)} partidos para analizar hoy.")
    print("\n📅 Lista de partidos válidos:")
    for f in fixtures:
        local = f['teams']['home']['name']
        visitante = f['teams']['away']['name']
        fixture_id = f['fixture']['id']
        print(f" - {local} vs {visitante} (Fixture ID: {fixture_id})")

