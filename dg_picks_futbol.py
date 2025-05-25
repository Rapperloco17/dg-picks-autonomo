
import requests
import os
from datetime import datetime
import pytz
import statistics

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Lista de ligas válidas
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
        valores = data["response"][0]["bookmakers"][0]["bets"][0]["values"]
        return valores
    except (IndexError, KeyError):
        return []

def convertir_horas(hora_utc_str):
    hora_utc = datetime.fromisoformat(hora_utc_str.replace("Z", "+00:00"))
    hora_mexico = hora_utc.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M")
    hora_espana = hora_utc.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
    return hora_mexico, hora_espana

def obtener_ultimos_partidos(equipo_id):
    url = f"{BASE_URL}/fixtures?team={equipo_id}&last=10"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    goles = []
    tiros = []
    posesion = []

    for match in data.get("response", []):
        if match["teams"]["home"]["id"] == equipo_id:
            goles.append(match["goals"]["home"])
        else:
            goles.append(match["goals"]["away"])
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

    promedio_goles = round(statistics.mean(goles), 2) if goles else "N/A"
    promedio_tiros = round(statistics.mean(tiros), 2) if tiros else "N/A"
    promedio_posesion = round(statistics.mean(posesion), 1) if posesion else "N/A"

    return {
        "goles_prom": promedio_goles,
        "tiros_prom": promedio_tiros,
        "posesion_prom": promedio_posesion,
        "forma": goles
    }

def obtener_h2h(equipo1_id, equipo2_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={equipo1_id}-{equipo2_id}&last=5"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    resultados = []
    for match in data.get("response", []):
        resultados.append(f"{match['teams']['home']['name']} {match['goals']['home']} - {match['goals']['away']} {match['teams']['away']['name']}")
    return resultados

if __name__ == "__main__":
    partidos = obtener_partidos_hoy()
    for p in partidos:
        cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)
        cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)
        cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)

        hora_mex, hora_esp = convertir_horas(p["hora_utc"])

        print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]}')
        print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')
        if len(cuotas_ml) >= 3:
            print(f'Cuotas: 🏠 {cuotas_ml[0]["odd"]} | 🤝 {cuotas_ml[1]["odd"]} | 🛫 {cuotas_ml[2]["odd"]}')
        else:
            print('Cuotas: 🏠 ❌ | 🤝 ❌ | 🛫 ❌')

        cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
        cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")
        print(f'Over 2.5: {cuota_over} | BTTS: {cuota_btts}')

        stats_local = obtener_ultimos_partidos(p["home_id"])
        stats_visitante = obtener_ultimos_partidos(p["away_id"])

        print(f'Forma {p["local"]}: {stats_local["forma"]} | Goles prom: {stats_local["goles_prom"]} | Tiros: {stats_local["tiros_prom"]} | Posesión: {stats_local["posesion_prom"]}%')
        print(f'Forma {p["visitante"]}: {stats_visitante["forma"]} | Goles prom: {stats_visitante["goles_prom"]} | Tiros: {stats_visitante["tiros_prom"]} | Posesión: {stats_visitante["posesion_prom"]}%')

        h2h = obtener_h2h(p["home_id"], p["away_id"])
        print("Últimos 5 enfrentamientos:")
        for r in h2h:
            print(f'🔹 {r}')
        print("-" * 60)
