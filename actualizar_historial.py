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

# --- Simulación de carga de historial por liga ---
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

# --- Simulación de actualización por liga ---
for liga_id, liga_nombre in ligas_validas.items():
    try:
        nuevos_partidos = True  # Aquí irá la lógica real

        if nuevos_partidos:
            print(f"✅ Historial actualizado para {liga_nombre} (ID: {liga_id})")
        else:
            print(f"⏩ Sin partidos nuevos para {liga_nombre} (ID: {liga_id})")
    except Exception as e:
        print(f"❌ Error actualizando {liga_nombre} (ID: {liga_id}): {e}")
