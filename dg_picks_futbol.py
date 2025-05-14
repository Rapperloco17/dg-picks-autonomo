import os
import json
import datetime
import requests
import re
import glob

# Cargar API key desde variables de entorno (Railway)
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

# Lista REAL con las 52 ligas oficiales del archivo Excel
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

# Paso 1: Verificar historial JSON
print("\n🔍 Verificando archivos históricos...")
faltan = []
presentes = []

for liga, liga_id in LIGAS_ESPERADAS.items():
    ruta = f"{RUTA_HISTORIAL}/resultados_{liga}.json"
    if os.path.exists(ruta):
        presentes.append(liga)
    else:
        faltan.append((liga, liga_id))

# Paso 1B: Descargar si falta algún historial
if faltan:
    print("\n📥 Faltan archivos, descargando historial desde la API...")
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    for liga, liga_id in faltan:
        try:
            url = f"{API_URL}/fixtures?league={liga_id}&season=2024&status=FT"
            res = requests.get(url, headers=HEADERS)
            data = res.json().get("response", [])
            os.makedirs(RUTA_HISTORIAL, exist_ok=True)
            with open(f"{RUTA_HISTORIAL}/resultados_{liga}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Historial guardado: {liga} ({len(data)} partidos)")
        except Exception as e:
            print(f"❌ Error descargando {liga}: {e}")
else:
    print("✅ Todos los archivos de historial están presentes.")

# Paso 2: Obtener partidos del día
print("\n📅 Buscando partidos del día...")
hoy = datetime.datetime.now().strftime("%Y-%m-%d")
response = requests.get(f"{API_URL}/fixtures?date={hoy}", headers=HEADERS)
fixtures = response.json().get("response", [])
print(f"📌 {len(fixtures)} partidos encontrados.")

# Paso 3: Cargar estadísticas históricas desde JSON
historial = {}
archivos_json = glob.glob(f"{RUTA_HISTORIAL}/resultados_*.json")
for archivo in archivos_json:
    clave = os.path.basename(archivo).replace("resultados_", "").replace(".json", "")
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            historial[clave] = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {clave}: {e}")

# Paso 4: Analizar cada fixture
for partido in fixtures:
    try:
        fixture_id = partido['fixture']['id']
        equipo_local = partido['teams']['home']['name']
        equipo_visita = partido['teams']['away']['name']
        liga_nombre = partido['league']['name']
        liga_clave = re.sub(r"[^a-z0-9_]", "_", liga_nombre.lower().replace(" ", "_"))

        if liga_clave not in historial:
            print(f"❌ No hay historial para {liga_nombre}, se salta.")
            continue

        print(f"\n🔎 Analizando: {equipo_local} vs {equipo_visita} ({liga_nombre})")

        # Paso 5: Obtener estadísticas del fixture
        stats_url = f"{API_URL}/fixtures/statistics?fixture={fixture_id}"
        stats_res = requests.get(stats_url, headers=HEADERS).json()
        tiros, posesion, corners, tarjetas = None, None, None, None
        for equipo in stats_res.get("response", []):
            stats = {s['type']: s['value'] for s in equipo.get('statistics', [])}
            if 'Total Shots' in stats:
                tiros = stats['Total Shots']
            if 'Ball Possession' in stats:
                posesion = stats['Ball Possession']
            if 'Corner Kicks' in stats:
                corners = stats['Corner Kicks']
            if 'Yellow Cards' in stats:
                tarjetas = stats['Yellow Cards']

        # Paso 6: Obtener cuotas
        odds_url = f"{API_URL}/odds?fixture={fixture_id}&bookmaker=1"
        odds_res = requests.get(odds_url, headers=HEADERS).json()
        cuotas = odds_res.get("response", [])

        # Paso 7: Cálculo tentativo (marcador, valor, forma)
        goles_local = 1.4  # Ejemplo simulado
        goles_visita = 1.1  # Ejemplo simulado
        marcador = f"{round(goles_local)} - {round(goles_visita)}"

        # Paso 8: Publicar (aún solo consola)
        print(f"Predicción tentativa: {marcador}")
        print(f"Tiros: {tiros}, Posesión: {posesion}, Corners: {corners}, Tarjetas: {tarjetas}")

    except Exception as e:
        print(f"❌ Error analizando partido: {e}")
