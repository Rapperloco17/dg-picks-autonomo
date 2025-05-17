import requests
import json
from datetime import datetime
from utils.prediccion_resultado import predecir_resultado
from utils.formatos_telegram import formatear_mensaje_partido
from utils.modelo_probabilidades import estimar_probabilidades_goles

# API key y URL de fixtures
API_KEY = "tu_api_key"
HEADERS = {"x-apisports-key": API_KEY}
URL_FIXTURES = "https://v3.football.api-sports.io/fixtures"

# Ligas permitidas (diccionario completo con 58 ligas)
ligas_permitidas = {
    1: "World Cup", 2: "UEFA Champions League", 3: "UEFA Europa League", 4: "Euro Championship",
    9: "Copa America", 11: "CONMEBOL Sudamericana", 13: "CONMEBOL Libertadores",
    16: "CONCACAF Champions League", 39: "Premier League", 40: "Championship",
    61: "Ligue 1", 62: "Ligue 2", 71: "Serie A", 72: "Serie B", 73: "Copa Do Brasil",
    45: "FA Cup", 78: "Bundesliga", 79: "2. Bundesliga", 88: "Eredivisie", 94: "Primeira Liga",
    103: "Eliteserien", 106: "Ekstraklasa", 113: "Allsvenskan", 119: "Superliga",
    128: "Liga Profesional Argentina", 129: "Primera Nacional", 130: "Copa Argentina",
    135: "Serie A", 136: "Serie B", 137: "Coppa Italia", 140: "La Liga",
    141: "Segunda División", 143: "Copa del Rey", 144: "Jupiler Pro League",
    162: "Primera División", 164: "Úrvalsdeild", 169: "Super League", 172: "First League",
    179: "Premiership", 188: "A-League", 197: "Super League 1", 203: "Süper Lig",
    207: "Super League", 210: "HNL", 218: "Bundesliga", 239: "Primera A",
    242: "Liga Pro", 244: "Veikkausliiga", 253: "Major League Soccer", 257: "US Open Cup",
    262: "Liga MX", 263: "Liga de Expansión MX", 265: "Primera División",
    268: "Primera División - Apertura", 271: "NB I", 281: "Primera División",
    345: "Czech Liga", 357: "Premier Division"
}

# Obtener fixtures de hoy
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
params = {"date": fecha_hoy}
response = requests.get(URL_FIXTURES, headers=HEADERS, params=params)
fixtures = response.json().get("response", [])

# Cargar historial por liga
import os
historial_por_liga = {}
unificados_path = "historial/unificados"
if os.path.exists(unificados_path):
    for archivo in os.listdir(unificados_path):
        if archivo.startswith("resultados_") and archivo.endswith(".json"):
            id_liga = archivo.replace("resultados_", "").replace(".json", "")
            try:
                id_liga_int = int(id_liga)
                if id_liga_int in ligas_permitidas:
                    with open(os.path.join(unificados_path, archivo), encoding="utf-8") as f:
                        historial_por_liga[id_liga_int] = json.load(f)
            except ValueError:
                continue

# Filtrar partidos válidos con historial disponible
partidos_validos = [fixture for fixture in fixtures if fixture["league"]["id"] in historial_por_liga]

# Guardar partidos válidos detectados (debug)
with open("partidos_validos_debug.json", "w", encoding="utf-8") as f:
    json.dump(partidos_validos, f, ensure_ascii=False, indent=4)

# Si no hay partidos válidos
if not partidos_validos:
    print("⚠️ Hoy no hubo partidos válidos con historial para analizar.")
else:
    print(f"📘 Partidos válidos en ligas activas con historial: {len(partidos_validos)}")
    for partido in partidos_validos:
        liga = partido["league"]["name"]
        local = partido["teams"]["home"]["name"]
        visitante = partido["teams"]["away"]["name"]
        print(f"{liga}: {local} vs {visitante}")

    # Aquí va la lógica de predicción de resultados, análisis y formateo para Telegram
