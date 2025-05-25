
import requests
import os
from datetime import datetime
import pytz
import statistics
import math

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
        liga_id = fixture["league"]["id"]
        if liga_id in LIGAS_VALIDAS:
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
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bet={bet_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    try:
        return data["response"][0]["bookmakers"][0]["bets"][0]["values"]
    except:
        return []

def convertir_horas(hora_utc_str):
    hora_utc = datetime.fromisoformat(hora_utc_str.replace("Z", "+00:00"))
    return (
        hora_utc.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M"),
        hora_utc.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
    )

def obtener_ultimos_partidos(equipo_id):
    url = f"{BASE_URL}/fixtures?team={equipo_id}&last=10"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    goles = []
    tiros = []
    posesion = []
    ganados = perdidos = empatados = 0

    for match in data.get("response", []):
        if match["teams"]["home"]["id"] == equipo_id:
            gf = match["goals"]["home"]
            gc = match["goals"]["away"]
        else:
            gf = match["goals"]["away"]
            gc = match["goals"]["home"]

        goles.append(gf)
        if gf > gc:
            ganados += 1
        elif gf < gc:
            perdidos += 1
        else:
            empatados += 1

        fixture_id = match["fixture"]["id"]
        stats_url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}&team={equipo_id}"
        stats_res = requests.get(stats_url, headers=HEADERS).json()
        try:
            for stat in stats_res["response"]["statistics"]:
                if stat["type"] == "Shots on Goal":
                    tiros.append(int(stat["value"]))
                if stat["type"] == "Ball Possession":
                    posesion.append(int(stat["value"].replace("%", "")))
        except:
            continue

    return {
        "goles_prom": round(statistics.mean(goles), 2) if goles else 0,
        "tiros_prom": round(statistics.mean(tiros), 2) if tiros else "N/A",
        "posesion_prom": round(statistics.mean(posesion), 1) if posesion else "N/A",
        "forma": goles,
        "ganados": ganados,
        "empatados": empatados,
        "perdidos": perdidos
    }

def obtener_h2h(equipo1_id, equipo2_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={equipo1_id}-{equipo2_id}&last=5"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return [
        f'{m["teams"]["home"]["name"]} {m["goals"]["home"]} - {m["goals"]["away"]} {m["teams"]["away"]["name"]}'
        for m in data.get("response", [])
    ]

def predecir_marcador(gl_home, gl_away):
    factor_local = 1.15
    factor_visit = 0.95
    goles_local = round(gl_home * factor_local)
    goles_away = round(gl_away * factor_visit)
    return goles_local, goles_away

def elegir_pick(goles_local, goles_away, cuota_over, cuota_btts, cuotas_ml):
    total_goles = goles_local + goles_away
    if total_goles >= 3 and cuota_over != "❌":
        return f"🎯 Pick sugerido: Over 2.5 goles @ {cuota_over}"
    elif goles_local >= 1 and goles_away >= 1 and cuota_btts != "❌":
        return f"🎯 Pick sugerido: Ambos Anotan (BTTS) @ {cuota_btts}"
    elif cuotas_ml and cuotas_ml[0] != "N/A":
        return f"🎯 Pick sugerido: Gana local @ {cuotas_ml[0]}"
    else:
        return "🎯 Pick sugerido: Sin valor claro"

if __name__ == "__main__":
    partidos = obtener_partidos_hoy()
    for p in partidos:
        cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)
        cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)
        cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)

        cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
        cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

        hora_mex, hora_esp = convertir_horas(p["hora_utc"])
        stats_local = obtener_ultimos_partidos(p["home_id"])
        stats_visitante = obtener_ultimos_partidos(p["away_id"])

        goles_local, goles_visitante = predecir_marcador(stats_local["goles_prom"], stats_visitante["goles_prom"])

        print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]}')
        print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')
        print(f'Cuotas: 🏠 {cuotas_ml[0]["odd"] if cuotas_ml else "❌"} | 🤝 {cuotas_ml[1]["odd"] if len(cuotas_ml)>1 else "❌"} | 🛫 {cuotas_ml[2]["odd"] if len(cuotas_ml)>2 else "❌"}')
        print(f'Over 2.5: {cuota_over} | BTTS: {cuota_btts}')
        print(f'Predicción marcador: {p["local"]} {goles_local} - {goles_visitante} {p["visitante"]}')
        print(elegir_pick(goles_local, goles_away=goles_visitante, cuota_over=cuota_over, cuota_btts=cuota_btts, cuotas_ml=cuotas_ml))
        print("-" * 60)
