
import requests
import os
from datetime import datetime
import pytz

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16,
    39, 40, 45, 61, 62, 71, 72, 73,
    78, 79, 88, 94, 103, 106, 113, 119,
    128, 129, 130, 135, 136, 137,
    140, 141, 143, 144, 162, 164, 169, 172,
    179, 188, 197, 203, 207, 210, 218, 239,
    242, 244, 253, 257, 262, 263, 265, 268,
    271, 281, 345, 357
]

def obtener_fixtures_hoy():
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    fixtures = [f for f in data['response'] if f['league']['id'] in LIGAS_VALIDAS]
    return fixtures

def obtener_estadisticas_partido(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", [])

def obtener_h2h(local_id, visitante_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={local_id}-{visitante_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", [])[:5]

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json().get("response", [])
    if not data:
        return None
    try:
        for bookmaker in data[0]["bookmakers"]:
            for bet in bookmaker["bets"]:
                if bet["name"] == "Match Winner":
                    return {o["value"]: float(o["odd"]) for o in bet["odds"]}
    except Exception:
        return None
    return None

def analizar_partido(f):
    fixture_id = f['fixture']['id']
    local = f['teams']['home']['name']
    visitante = f['teams']['away']['name']
    league = f['league']['name']
    hora = f['fixture']['timestamp']
    hora_local = datetime.fromtimestamp(hora).strftime("%H:%M")

    cuotas = obtener_cuotas(fixture_id)
    if not cuotas:
        print(f"⚠️ No se encontraron cuotas para el partido {local} vs {visitante}")
        return None

    if not any(1.40 <= cuotas.get(t, 0) <= 4.00 for t in cuotas):
        print(f"❌ Cuotas fuera de rango para el partido {local} vs {visitante}")
        return None

    stats = obtener_estadisticas_partido(fixture_id)
    if len(stats) < 2:
        print(f"⚠️ No hay estadísticas suficientes para el partido {local} vs {visitante}")
        return None

    tiros_local = next((int(s['statistics'][0]['value']) for s in stats if s['team']['name'] == local and s['statistics'][0]['type'] == "Shots on Goal"), None)
    tiros_visitante = next((int(s['statistics'][0]['value']) for s in stats if s['team']['name'] == visitante and s['statistics'][0]['type'] == "Shots on Goal"), None)

    posesion_local = next((int(s['statistics'][9]['value'].replace('%','')) for s in stats if s['team']['name'] == local and s['statistics'][9]['type'] == "Ball Possession"), None)
    posesion_visitante = next((int(s['statistics'][9]['value'].replace('%','')) for s in stats if s['team']['name'] == visitante and s['statistics'][9]['type'] == "Ball Possession"), None)

    h2h = obtener_h2h(f['teams']['home']['id'], f['teams']['away']['id'])
    victorias_local = sum(1 for match in h2h if match['teams']['home']['name'] == local and match['teams']['home']['winner'])
    victorias_visitante = sum(1 for match in h2h if match['teams']['away']['name'] == visitante and match['teams']['away']['winner'])

    mensaje = f"🏟️ {local} vs {visitante} ({league})\n🕘 Hora: {hora_local}\n"
    mensaje += f"📊 Tiros a gol: {local} {tiros_local} - {tiros_visitante} {visitante}\n"
    mensaje += f"📊 Posesión: {local} {posesion_local}% - {posesion_visitante}% {visitante}\n"
    mensaje += f"📈 Últimos H2H: {victorias_local} victorias {local} / {victorias_visitante} {visitante}\n"
    mensaje += f"💸 Cuotas ML: {local} @ {cuotas.get(local)} | Empate @ {cuotas.get('Draw')} | {visitante} @ {cuotas.get(visitante)}\n"

    mejor_equipo = local if victorias_local >= victorias_visitante else visitante
    cuota_mejor = cuotas.get(mejor_equipo)
    if cuota_mejor and 1.40 <= cuota_mejor <= 4.00:
        mensaje += f"✅ Pick: {mejor_equipo} ML\n✅ Valor detectado en la cuota"
        return mensaje
    return None

# 🔥 Ejecutar
fixtures = obtener_fixtures_hoy()
for f in fixtures:
    try:
        analisis = analizar_partido(f)
        if analisis:
            print(analisis)
            print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"❌ Error inesperado analizando partido {f['teams']['home']['name']} vs {f['teams']['away']['name']}: {e}")
