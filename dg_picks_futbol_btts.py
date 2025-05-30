
import requests
import os
from datetime import datetime
import pytz
import statistics
import traceback

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_partidos_hoy():
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    partidos_validos = []
    for fixture in data.get("response", []):
        if fixture["league"]["id"] in LIGAS_VALIDAS:
            if fixture["fixture"]["status"]["short"] != "NS":
                continue
            partidos_validos.append({
                "liga": fixture["league"]["name"],
                "local": fixture["teams"]["home"]["name"],
                "visitante": fixture["teams"]["away"]["name"],
                "hora_utc": fixture["fixture"]["date"],
                "id_fixture": fixture["fixture"]["id"],
                "home_id": fixture["teams"]["home"]["id"],
                "away_id": fixture["teams"]["away"]["id"]
            })
    return partidos_validos

def obtener_cuotas_por_mercado(fixture_id, bet_id):
    try:
        url = f"{BASE_URL}/odds?fixture={fixture_id}&bet={bet_id}"
        response = requests.get(url, headers=HEADERS)
        return response.json()["response"][0]["bookmakers"][0]["bets"][0]["values"]
    except:
        return []

def convertir_horas(hora_utc_str):
    hora_utc = datetime.fromisoformat(hora_utc_str.replace("Z", "+00:00"))
    return (
        hora_utc.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M"),
        hora_utc.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
    )

def calcular_probabilidades_btts_over(equipo_id, condicion):
    url = f"https://v3.football.api-sports.io/fixtures?team={equipo_id}&last=20"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    btts_count = 0
    over25_count = 0
    total_partidos = 0

    for match in data.get("response", []):
        if condicion == "local" and match["teams"]["home"]["id"] != equipo_id:
            continue
        if condicion == "visitante" and match["teams"]["away"]["id"] != equipo_id:
            continue

        goles_local = match["goals"]["home"]
        goles_visitante = match["goals"]["away"]

        if goles_local is None or goles_visitante is None:
            continue

        total_partidos += 1
        if goles_local + goles_visitante >= 3:
            over25_count += 1
        if goles_local > 0 and goles_visitante > 0:
            btts_count += 1

    if total_partidos == 0:
        return {"btts": 0, "over": 0}
    return {
        "btts": round((btts_count / total_partidos) * 100),
        "over": round((over25_count / total_partidos) * 100)
    }

if __name__ == "__main__":
    try:
        partidos = obtener_partidos_hoy()
        for p in partidos:
            print(f"⏱️ Analizando: {p['local']} vs {p['visitante']}")

            cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)
            cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

            hora_mex, hora_esp = convertir_horas(p["hora_utc"])
            print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')

            prob_local = calcular_probabilidades_btts_over(p["home_id"], "local")
            prob_away = calcular_probabilidades_btts_over(p["away_id"], "visitante")
            print(f'📊 Probabilidades (últimos 20 partidos):')
            print(f'- {p["local"]}: BTTS {prob_local["btts"]}% | Over 2.5 {prob_local["over"]}%')
            print(f'- {p["visitante"]}: BTTS {prob_away["btts"]}% | Over 2.5 {prob_away["over"]}%')

            btts_local = prob_local["btts"]
            btts_visit = prob_away["btts"]

            if btts_local >= 70 and btts_visit >= 70:
                print(f"✅ BTTS: Sí (Alta probabilidad)")
                if cuota_btts != "❌":
                    print(f"🎯 PICK BTTS: Ambos anotan @ {cuota_btts}")
                    print("✅ Valor detectado en la cuota")
            elif (
                (btts_local >= 70 and btts_visit >= 55) or
                (btts_visit >= 70 and btts_local >= 55)
            ):
                print(f"✅ BTTS: Sí (Probabilidad moderada)")
                if cuota_btts != "❌":
                    print(f"🎯 PICK BTTS: Ambos anotan @ {cuota_btts}")
                    print("⚠️ Valor aceptable, revisar contexto")
            else:
                print(f"❌ BTTS: No (Baja probabilidad)")

            print("-" * 60)

    except Exception as e:
        print("❌ Error crítico:")
        traceback.print_exc()
