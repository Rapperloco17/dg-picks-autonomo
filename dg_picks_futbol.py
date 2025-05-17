import requests
import datetime
import json
import os
import time

# Lista de ligas válidas con sus IDs y nombres oficiales
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
    218: "Bundesliga (Austria)",
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
    281: "Primera División (Panamá)",
    345: "Czech Liga",
    357: "Premier Division"
}

# Obtener fixtures del día desde API
API_KEY = os.getenv("API_FOOTBALL_KEY")
headers = {"x-apisports-key": API_KEY}
fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
url = f"https://v3.football.api-sports.io/fixtures?date={fecha_hoy}"
response = requests.get(url, headers=headers)
data = response.json()
fixtures = data.get("response", [])

# Cargar historial
historial_por_liga = {}
for archivo in os.listdir("historial/unificados"):
    if archivo.startswith("resultados_") and archivo.endswith(".json"):
        lid = int(archivo.replace("resultados_", "").replace(".json", ""))
        if lid in ligas_validas:
            with open(f"historial/unificados/{archivo}", "r", encoding="utf-8") as f:
                historial_por_liga[lid] = json.load(f)

# Filtrar partidos válidos con historial
partidos_validos = [f for f in fixtures if f["league"]["id"] in historial_por_liga]

# Guardar para debug
with open("partidos_validos_debug.json", "w", encoding="utf-8") as f:
    json.dump(partidos_validos, f, ensure_ascii=False, indent=4)

# Imprimir resultados
if not partidos_validos:
    print("⚠️ Hoy no hubo partidos válidos con historial para analizar.")
else:
    print(f"📘 Partidos válidos en ligas activas con historial: {len(partidos_validos)}")
    for p in partidos_validos:
        lid = p["league"]["id"]
        local = p["teams"]["home"]["name"]
        visita = p["teams"]["away"]["name"]
        liga = ligas_validas.get(lid, p["league"]["name"])
        print(f"{liga}: {local} vs {visita}")
