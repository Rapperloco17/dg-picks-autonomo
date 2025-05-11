import requests
from datetime import datetime
import time
import json
import os

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
LIGAS_VALIDAS = {
    39, 61, 78, 135, 140, 2, 3, 4, 5, 16, 45, 71, 72, 135,
    253, 262, 203, 88, 94, 271, 1139, 1439
}

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def obtener_cuotas_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    cuotas = {}
    for book in res.json().get("response", []):
        for bookmaker in book.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                nombre = bet.get("name", "").lower()
                for val in bet.get("values", []):
                    key = f"{nombre}_{val.get('value', '').lower()}"
                    cuotas[key] = float(val.get("odd", 0))
    return cuotas

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
    goles = pred.get("predictions", {}).get("goals", {}).get("total", 0)
    btts = pred.get("predictions", {}).get("both_teams_to_score", {}).get("yes", "0%")
    forma_local = pred.get("teams", {}).get("home", {}).get("last_5", {}).get("form", "")
    forma_visita = pred.get("teams", {}).get("away", {}).get("last_5", {}).get("form", "")

    resultado = {
        "partido": matchup,
        "cuotas": {
            "over_2.5": cuotas.get("over 2.5", None),
            "under_2.5": cuotas.get("under 2.5", None),
            "1X": cuotas.get("double chance_1x", None),
            "X2": cuotas.get("double chance_x2", None),
            "12": cuotas.get("double chance_12", None),
            "btts": cuotas.get("both teams to score_yes", None)
        },
        "estadisticas": {
            "promedio_goles": goles,
            "prob_btts": btts,
            "forma_local": forma_local,
            "forma_visitante": forma_visita
        },
        "prediccion_api": pred.get("predictions", {}).get("winner", {}).get("name", "Sin datos")
    }

    # Lógica de pick
    pick = None
    if goles > 2.5 and resultado["cuotas"].get("over_2.5"):
        pick = {
            "tipo": "Over 2.5 goles",
            "cuota": resultado["cuotas"]["over_2.5"],
            "motivo": "Promedio alto de goles en el partido"
        }
    elif btts and int(btts.replace("%", "")) >= 65 and resultado["cuotas"].get("btts"):
        pick = {
            "tipo": "Ambos anotan",
            "cuota": resultado["cuotas"]["btts"],
            "motivo": "Probabilidad alta de BTTS según API"
        }

    if pick:
        resultado["pick_generado"] = pick

    return resultado

print("\n🔍 Buscando partidos del día...")
fixtures = obtener_fixtures_hoy()
resultados_completos = []
picks_finales = []

for partido in fixtures:
    liga_id = partido["league"]["id"]
    if liga_id not in LIGAS_VALIDAS:
        continue
    fixture_id = partido["fixture"]["id"]
    try:
        cuotas = obtener_cuotas_fixture(fixture_id)
        pred = obtener_predicciones(fixture_id)
        analisis = generar_pick_completo(partido, cuotas, pred)

        print(f"\n🆚 Partido: {analisis['partido']}")
        print("📊 Cuotas clave:")
        for k, v in analisis['cuotas'].items():
            print(f"   - {k}: {v}")
        print(f"📉 Predicción API: {analisis['prediccion_api']}")
        print("📈 Estadísticas:")
        for k, v in analisis['estadisticas'].items():
            print(f"   - {k}: {v}")
        if "pick_generado" in analisis:
            print(f"\n✅ Pick generado: {analisis['pick_generado']['tipo']} @ {analisis['pick_generado']['cuota']}")
            print(f"🧠 Motivo: {analisis['pick_generado']['motivo']}")
            picks_finales.append({
                "partido": analisis["partido"],
                "pick": analisis["pick_generado"]["tipo"],
                "cuota": analisis["pick_generado"]["cuota"],
                "motivo": analisis["pick_generado"]["motivo"],
                "fecha_generacion": datetime.now().isoformat()
            })
        else:
            print("❌ No se generó pick con valor")

        resultados_completos.append(analisis)
        time.sleep(1.2)

    except Exception as e:
        print(f"❌ Error en fixture {fixture_id}: {e}")

# Guardar análisis completo
os.makedirs("output", exist_ok=True)
with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
    json.dump(picks_finales, f, indent=4, ensure_ascii=False)

print("\n✅ Análisis finalizado. Picks guardados en output/picks_futbol.json")
