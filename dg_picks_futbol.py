import os
import json
import datetime
import requests
from descargar_resultados_por_liga import descargar_historial_de_ligas_top

# Cargar API key desde variables de entorno (Railway)
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

# Telegram (si quieres activar envío con token desde Railway también)
# from bot import enviar_mensaje

# Constantes
LIGAS_ESPERADAS = [
    "premier_league", "laliga", "serie_a", "bundesliga", "ligue_1",
    "argentina", "brasil", "mls", "libertadores", "sudamericana",
    "eredivisie", "championship", "copa_america", "euro_championship"
]
RUTA_HISTORIAL = "historial/unificados"
API_URL = "https://v3.football.api-sports.io"

# Paso 1: Verificar historial JSON
print("\n🔍 Verificando archivos históricos...")
faltan = []
presentes = []
for liga in LIGAS_ESPERADAS:
    ruta = f"{RUTA_HISTORIAL}/resultados_{liga}.json"
    if os.path.exists(ruta):
        presentes.append(liga)
    else:
        faltan.append(liga)

if faltan:
    print("\n⛔ Faltan archivos:", faltan)
    print("📥 Descargando historial...")
    descargar_historial_de_ligas_top()
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
for liga in LIGAS_ESPERADAS:
    ruta = f"{RUTA_HISTORIAL}/resultados_{liga}.json"
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            historial[liga] = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {liga}: {e}")

# Paso 4: Analizar cada fixture
for partido in fixtures:
    try:
        fixture_id = partido['fixture']['id']
        equipo_local = partido['teams']['home']['name']
        equipo_visita = partido['teams']['away']['name']
        liga_nombre = partido['league']['name']
        liga_id = partido['league']['id']
        liga_clave = liga_nombre.lower().replace(" ", "_").replace("-", "_")

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
        # Aquí conectas con tus datos históricos para sacar forma y promedios
        goles_local = 1.4  # Ejemplo simulado
        goles_visita = 1.1  # Ejemplo simulado

        marcador = f"{round(goles_local)} - {round(goles_visita)}"

        # Paso 8: Publicar (aún solo consola)
        print(f"Predicción tentativa: {marcador}")
        print(f"Tiros: {tiros}, Posesión: {posesion}, Corners: {corners}, Tarjetas: {tarjetas}")
        # enviar_mensaje("canal_id", mensaje_formateado)  # cuando actives Telegram

    except Exception as e:
        print(f"❌ Error analizando partido: {e}")

