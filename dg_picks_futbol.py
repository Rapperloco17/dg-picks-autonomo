import os
import json
import datetime
import requests
import re
import glob
import statistics
from collections import defaultdict

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

LIGAS_ESPERADAS = {
    'world_cup': 1, 'uefa_champions_league': 2, 'uefa_europa_league': 3, 'euro_championship': 4,
    'copa_america': 9, 'conmebol_sudamericana': 11, 'conmebol_libertadores': 13,
    'concacaf_champions_league': 16, 'premier_league': 39, 'championship': 40,
    'ligue_1': 61, 'ligue_2': 62, 'serie_a': 135, 'serie_b': 136, 'copa_do_brasil': 73,
    'fa_cup': 45, 'bundesliga': 218, '2__bundesliga': 79, 'eredivisie': 88,
    'primeira_liga': 94, 'eliteserien': 103, 'ekstraklasa': 106, 'allsvenskan': 113,
    'superliga': 119, 'liga_profesional_argentina': 128, 'primera_nacional': 129,
    'copa_argentina': 130, 'coppa_italia': 137, 'la_liga': 140, 'segunda_divisi_n': 141,
    'copa_del_rey': 143, 'jupiler_pro_league': 144, 'primera_divisi_n': 281,
    '_rvalsdeild': 164, 'super_league': 207, 'first_league': 172, 'premiership': 179,
    'a_league': 188, 'super_league_1': 197, 's_per_lig': 203, 'hnl': 210,
    'primera_a': 239, 'liga_pro': 242, 'veikkausliiga': 244, 'major_league_soccer': 253,
    'us_open_cup': 257, 'liga_mx': 262, 'liga_de_expansi_n_mx': 263,
    'primera_divisi_n___apertura': 268, 'nb_i': 271, 'czech_liga': 345,
    'premier_division': 357
}

RUTA_HISTORIAL = "historial/unificados"
API_URL = "https://v3.football.api-sports.io"

# Cargar JSONs históricos
historial = {}
archivos_json = glob.glob(f"{RUTA_HISTORIAL}/resultados_*.json")
for archivo in archivos_json:
    clave = os.path.basename(archivo).replace("resultados_", "").replace(".json", "")
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            historial[clave] = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {clave}: {e}")

# Analizar rendimiento por equipo a partir del historial
def calcular_estadisticas_equipo(juegos, equipo_nombre, condicion):
    goles_favor, goles_contra, btts, overs = [], [], 0, 0
    for partido in juegos:
        try:
            home = partido['teams']['home']['name']
            away = partido['teams']['away']['name']
            g_home = partido['goals']['home']
            g_away = partido['goals']['away']

            if condicion == 'local' and home == equipo_nombre:
                goles_favor.append(g_home)
                goles_contra.append(g_away)
                if g_home > 0 and g_away > 0: btts += 1
                if (g_home + g_away) >= 2.5: overs += 1

            elif condicion == 'visitante' and away == equipo_nombre:
                goles_favor.append(g_away)
                goles_contra.append(g_home)
                if g_home > 0 and g_away > 0: btts += 1
                if (g_home + g_away) >= 2.5: overs += 1
        except:
            continue

    total = len(goles_favor)
    if total == 0:
        return None

    return {
        'juegos': total,
        'goles_favor': round(statistics.mean(goles_favor), 2) if goles_favor else 0,
        'goles_contra': round(statistics.mean(goles_contra), 2) if goles_contra else 0,
        'btts_pct': round((btts / total) * 100, 1),
        'over25_pct': round((overs / total) * 100, 1)
    }

# Obtener partidos del día
hoy = datetime.datetime.now().strftime("%Y-%m-%d")
res = requests.get(f"{API_URL}/fixtures?date={hoy}", headers=HEADERS)
fixtures = res.json().get("response", [])

for partido in fixtures:
    try:
        lid = partido['league']['id']
        lname = partido['league']['name']
        fixture_id = partido['fixture']['id']
        home = partido['teams']['home']['name']
        away = partido['teams']['away']['name']

        liga_clave = re.sub(r"[^a-z0-9_]", "_", lname.lower().replace(" ", "_"))
        if liga_clave not in historial:
            continue

        historial_liga = historial[liga_clave]
        stats_home = calcular_estadisticas_equipo(historial_liga, home, 'local')
        stats_away = calcular_estadisticas_equipo(historial_liga, away, 'visitante')

        if not stats_home or not stats_away:
            continue

        condiciones = []
        if stats_home['over25_pct'] >= 65 and stats_away['over25_pct'] >= 60:
            condiciones.append('Over 2.5')
        if stats_home['btts_pct'] >= 60 and stats_away['btts_pct'] >= 60:
            condiciones.append('Ambos anotan')
        if stats_home['goles_favor'] >= 1.5 and stats_away['goles_contra'] >= 1.5:
            condiciones.append(f"Gana {home}")

        if condiciones:
            print(f"\n📊 {home} vs {away} ({lname})")
            print(f"📌 Stats Local: {stats_home}")
            print(f"📌 Stats Visitante: {stats_away}")
            print(f"✅ Pick sugerido: {condiciones[0]} (valor detectado)")
        else:
            print(f"\n🚫 {home} vs {away}: No hay suficiente respaldo estadístico para un pick.")

    except Exception as e:
        print(f"❌ Error en análisis del fixture: {e}")
