import requests
import json
from datetime import datetime
import unicodedata
import os
import glob
import pandas as pd

# --- Normalizar nombres de equipo ---
def normalizar(nombre):
    nombre = nombre.lower().replace(".", "").replace("'", "").replace("-", "").replace("’", "")
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("utf-8")
    return nombre.replace(" ", "")

# --- Lista completa de ligas válidas con nombre (final 58) ---
ligas_validas = {
    1: "World Cup",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    4: "Euro Championship",
    9: "Copa America",
    11: "CONMEBOL Sudamericana",
    13: "CONMEBOL Libertadores",
    16: "CONCACAF Champions League",
    39: "Premier League",
    40: "Championship",
    45: "FA Cup",
    61: "Ligue 1",
    62: "Ligue 2",
    71: "Serie A",
    72: "Serie B",
    73: "Copa Do Brasil",
    78: "Bundesliga",
    79: "2. Bundesliga",
    88: "Eredivisie",
    94: "Primeira Liga",
    103: "Eliteserien",
    106: "Ekstraklasa",
    113: "Allsvenskan",
    119: "Superliga",
    128: "Liga Profesional Argentina",
    129: "Primera Nacional",
    130: "Copa Argentina",
    135: "Serie A",
    136: "Serie B",
    137: "Coppa Italia",
    140: "La Liga",
    141: "Segunda División",
    143: "Copa del Rey",
    144: "Jupiler Pro League",
    162: "Primera División",
    164: "Úrvalsdeild",
    169: "Super League",
    172: "First League",
    179: "Premiership",
    188: "A-League",
    197: "Super League 1",
    203: "Süper Lig",
    207: "Super League",
    210: "HNL",
    218: "Bundesliga",
    239: "Primera A",
    242: "Liga Pro",
    244: "Veikkausliiga",
    253: "Major League Soccer",
    257: "US Open Cup",
    262: "Liga MX",
    263: "Liga de Expansión MX",
    265: "Primera División",
    268: "Primera División - Apertura",
    271: "NB I",
    281: "Primera División",
    345: "Czech Liga",
    357: "Premier Division"
}

# --- Cargar historial por liga ---
historico_por_liga = {}
files = glob.glob("historial/unificados/resultados_*.json")
for file in files:
    try:
        lid = int(file.split("_")[-1].replace(".json", ""))
        if lid in ligas_validas:
            with open(file, "r", encoding="utf-8") as f:
                historico_por_liga[lid] = json.load(f)
    except ValueError:
        continue

# --- Fecha actual ---
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# --- Obtener partidos del día desde API ---
url = f"https://v3.football.api-sports.io/fixtures?date={fecha_hoy}"
headers = {
    "x-apisports-key": os.getenv("API_FOOTBALL_KEY")  # Asegúrate de tener la API key en variables de entorno
}
response = requests.get(url, headers=headers)
data = response.json()
fixtures = [f for f in data.get("response", []) if f["fixture"]["status"]["short"] == "NS"]

print("📆 Partidos válidos en ligas activas con historial:\n")
partidos_validos = []
for f in fixtures:
    lid = f["league"]["id"]
    if lid in historico_por_liga:
        local = f["teams"]["home"]["name"]
        visita = f["teams"]["away"]["name"]
        liga = f["league"]["name"]
        print(f"{local} vs {visita} — {liga} (ID: {lid})")
        partidos_validos.append((f, lid))

if not partidos_validos:
    print("⚠️ Hoy no hubo partidos válidos con historial para analizar.")
    exit()

# --- Funciones para cálculo ---
def calcular_promedios(partidos, equipo):
    gf = gc = 0
    for p in partidos:
        if equipo in p["teams"]["home"]["name"]:
            gf += p["goals"]["home"]
            gc += p["goals"]["away"]
        else:
            gf += p["goals"]["away"]
            gc += p["goals"]["home"]
    pj = len(partidos)
    return round(gf / pj, 2), round(gc / pj, 2)

def calcular_forma(partidos, equipo):
    puntos = 0
    for p in partidos[-5:]:
        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]
        gh = p["goals"]["home"]
        ga = p["goals"]["away"]
        if equipo in home:
            if gh > ga:
                puntos += 3
            elif gh == ga:
                puntos += 1
        elif equipo in away:
            if ga > gh:
                puntos += 3
            elif gh == ga:
                puntos += 1
    return puntos

def calcular_bttover(partidos):
    btts = over = 0
    for p in partidos:
        g1 = p["goals"]["home"]
        g2 = p["goals"]["away"]
        if g1 >= 0 and g2 >= 0:
            if g1 + g2 > 2.5:
                over += 1
            if g1 > 0 and g2 > 0:
                btts += 1
    total = len(partidos)
    return round((btts / total) * 100, 1), round((over / total) * 100, 1)

# --- Análisis ---
for fixture, lid in partidos_validos:
    equipo_local = fixture["teams"]["home"]["name"]
    equipo_visita = fixture["teams"]["away"]["name"]
    partidos = historico_por_liga[lid]

    equipo_local_norm = normalizar(equipo_local)
    equipo_visita_norm = normalizar(equipo_visita)

    prev_local = [p for p in partidos if equipo_local_norm == normalizar(p["teams"]["home"]["name"]) or equipo_local_norm == normalizar(p["teams"]["away"]["name"])]
    prev_visita = [p for p in partidos if equipo_visita_norm == normalizar(p["teams"]["home"]["name"]) or equipo_visita_norm == normalizar(p["teams"]["away"]["name"])]

    if not prev_local or not prev_visita:
        print(f"⚠️ Sin historial suficiente para: {equipo_local} o {equipo_visita}\n")
        continue

    gf_l, gc_l = calcular_promedios(prev_local, equipo_local)
    gf_v, gc_v = calcular_promedios(prev_visita, equipo_visita)
    forma_l = calcular_forma(prev_local, equipo_local)
    forma_v = calcular_forma(prev_visita, equipo_visita)
    btts_l, over_l = calcular_bttover(prev_local)
    btts_v, over_v = calcular_bttover(prev_visita)

    print(f"\n📊 {equipo_local} vs {equipo_visita}")
    print(f"Promedio goles {equipo_local}: {gf_l} GF / {gc_l} GC")
    print(f"Promedio goles {equipo_visita}: {gf_v} GF / {gc_v} GC")
    print(f"Forma reciente {equipo_local}: {forma_l} pts (últimos 5)")
    print(f"Forma reciente {equipo_visita}: {forma_v} pts (últimos 5)")
    print(f"BTTS %: {equipo_local} = {btts_l}%, {equipo_visita} = {btts_v}%")
    print(f"Over 2.5 %: {equipo_local} = {over_l}%, {equipo_visita} = {over_v}%")

    sugerencia = "Sin pick claro basado en datos"
    if btts_l > 60 and btts_v > 60:
        sugerencia = "Ambos anotan (BTTS)"
    elif over_l > 60 and over_v > 60:
        sugerencia = "Over 2.5 goles"
    elif gf_l > 1.5 and gc_v > 1.2:
        sugerencia = f"Gana {equipo_local}"
    elif gf_v > 1.5 and gc_l > 1.2:
        sugerencia = f"Gana {equipo_visita}"

    print(f"🎯 Pick sugerido: {sugerencia}")
    print("✅ Análisis completo para este partido\n")

    print(f"🎯 Pick sugerido: {sugerencia}")
    print("✅ Análisis completo para este partido\n")

