import requests
from datetime import datetime
import time

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# Ligas permitidas (whitelist)
LIGAS_VALIDAS = {
    39, 61, 78, 135, 140, 2, 3, 4, 5, 16, 45, 71, 72, 135, 253, 262, 203, 88, 94, 253, 271, 1139, 1439
}

# Funciones auxiliares
def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    return data.get("response", [])

def obtener_cuotas_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    odds = {}
    for book in data.get("response", []):
        for mercado in book.get("bookmakers", []):
            for apuesta in mercado.get("bets", []):
                nombre = apuesta.get("name", "").lower()
                for val in apuesta.get("values", []):
                    odds[nombre] = float(val.get("odd", 0))
    return odds

def obtener_predicciones(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    if data.get("response"):
        return data["response"][0]
    return {}

def generar_pick(fixture, cuotas, pred):
    local = fixture["teams"]["home"]["name"]
    visita = fixture["teams"]["away"]["name"]
    matchup = f"{local} vs {visita}"

    pred_ganador = pred.get("predictions", {}).get("winner", {}).get("name", "")
    win_percent = pred.get("predictions", {}).get("winner", {}).get("percent", 0)
    goles = pred.get("predictions", {}).get("goals", {}).get("total", 0)
    recomendacion = pred.get("predictions", {}).get("advice", "")

    picks = []
    if win_percent and int(win_percent) >= 60:
        if pred_ganador == local and "home" in cuotas:
            picks.append((matchup, f"Gana {local}", cuotas["home"], recomendacion))
        elif pred_ganador == visita and "away" in cuotas:
            picks.append((matchup, f"Gana {visita}", cuotas["away"], recomendacion))
    if goles:
        if goles > 2.5 and "over 2.5" in cuotas:
            picks.append((matchup, "Over 2.5 goles", cuotas["over 2.5"], recomendacion))
        elif goles <= 2.5 and "under 2.5" in cuotas:
            picks.append((matchup, "Under 2.5 goles", cuotas["under 2.5"], recomendacion))
    return picks

# Flujo principal
print("\n🔍 Buscando partidos del día...")
fixtures = obtener_fixtures_hoy()
picks_generados = []

for partido in fixtures:
    liga_id = partido["league"]["id"]
    if liga_id not in LIGAS_VALIDAS:
        continue

    fixture_id = partido["fixture"]["id"]
    try:
        cuotas = obtener_cuotas_fixture(fixture_id)
        pred = obtener_predicciones(fixture_id)
        picks = generar_pick(partido, cuotas, pred)
        picks_generados.extend(picks)
        time.sleep(1.2)
    except Exception as e:
        print(f"❌ Error con fixture {fixture_id}: {e}")

print("\n🎯 Picks Generados:")
for m, pick, cuota, razon in picks_generados:
    print(f"\nPartido: {m}\nPick: {pick} @ {cuota}\nJustificación: {razon}\n✅ Valor detectado")

if not picks_generados:
    print("\n⚠️ No se encontraron picks con valor para hoy.")
