import requests
from datetime import datetime
import time
import json

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

LIGAS_VALIDAS = {
    39, 61, 78, 135, 140, 2, 3, 4, 5, 16, 45, 71, 72, 135, 253, 262, 203, 88, 94, 253, 271, 1139, 1439
}

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def obtener_cuotas_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    odds = {}
    for book in res.json().get("response", []):
        for mercado in book.get("bookmakers", []):
            for apuesta in mercado.get("bets", []):
                nombre = apuesta.get("name", "").lower()
                for val in apuesta.get("values", []):
                    odds[nombre] = float(val.get("odd", 0))
    return odds

def obtener_predicciones(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    if res.json().get("response"):
        return res.json()["response"][0]
    return {}

def generar_pick_completo(fixture, cuotas, pred):
    local = fixture["teams"]["home"]["name"]
    visita = fixture["teams"]["away"]["name"]
    matchup = f"{local} vs {visita}"
    resultado = {
        "partido": matchup,
        "cuotas": cuotas,
        "prediccion_api": pred.get("predictions", {}).get("winner", {}).get("name", "Sin datos"),
        "estadisticas": {
            "promedio_goles": pred.get("predictions", {}).get("goals", {}).get("total", 0),
            "prob_btts": pred.get("predictions", {}).get("both_teams_to_score", {}).get("yes", "0%"),
            "forma_local": pred.get("teams", {}).get("home", {}).get("last_5", {}).get("form", ""),
            "forma_visitante": pred.get("teams", {}).get("away", {}).get("last_5", {}).get("form", "")
        }
    }
    # lógica de pick
    goles = resultado["estadisticas"]["promedio_goles"]
    btts = resultado["estadisticas"]["prob_btts"]
    pick = None
    if goles > 2.5 and "over 2.5" in cuotas:
        pick = {
            "pick": "Over 2.5 goles",
            "cuota": cuotas["over 2.5"],
            "motivo": "Promedio de goles alto y equipos ofensivos"
        }
    elif isinstance(btts, str) and int(btts.replace("%", "")) >= 65 and "both teams to score" in cuotas:
        pick = {
            "pick": "Ambos anotan",
            "cuota": cuotas["both teams to score"],
            "motivo": "Probabilidad alta de BTTS según API"
        }
    if pick:
        resultado["pick_generado"] = pick
    return resultado

print("\n🔍 Buscando partidos del día...")
fixtures = obtener_fixtures_hoy()
todos_resultados = []

for partido in fixtures:
    liga_id = partido["league"]["id"]
    if liga_id not in LIGAS_VALIDAS:
        continue
    fixture_id = partido["fixture"]["id"]
    try:
        cuotas = obtener_cuotas_fixture(fixture_id)
        pred = obtener_predicciones(fixture_id)
        resultado = generar_pick_completo(partido, cuotas, pred)

        print(f"\n📊 Partido: {resultado['partido']}")
        print("📈 Cuotas:")
        for k, v in resultado['cuotas'].items():
            print(f"   - {k}: {v}")
        print(f"📉 Predicción API: {resultado['prediccion_api']}")
        print("📊 Estadísticas:")
        for k, v in resultado['estadisticas'].items():
            print(f"   - {k}: {v}")
        if "pick_generado" in resultado:
            print(f"\n✅ Pick generado: {resultado['pick_generado']['pick']} @ {resultado['pick_generado']['cuota']}")
            print(f"🧠 Motivo: {resultado['pick_generado']['motivo']}")
        else:
            print("❌ No se generó pick con valor")

        todos_resultados.append(resultado)
        time.sleep(1.2)

    except Exception as e:
        print(f"❌ Error en fixture {fixture_id}: {e}")

# Guardar resultados
with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
    json.dump(todos_resultados, f, indent=4, ensure_ascii=False)

print("\n✅ Análisis completo finalizado. Resultados guardados en picks_futbol.json")

