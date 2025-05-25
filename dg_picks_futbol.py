
import requests
import os
from datetime import datetime
import pytz
import statistics

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
    try:
        return response.json()["response"][0]["bookmakers"][0]["bets"][0]["values"]
    except:
        return []

def convertir_horas(hora_utc_str):
    hora_utc = datetime.fromisoformat(hora_utc_str.replace("Z", "+00:00"))
    return (
        hora_utc.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M"),
        hora_utc.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
    )

def obtener_estadisticas_equipo(equipo_id):
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
                if stat["type"] == "Shots on Goal" and stat["value"]:
                    tiros.append(int(stat["value"]))
                if stat["type"] == "Ball Possession" and stat["value"]:
                    posesion.append(int(stat["value"].replace("%", "")))
        except:
            continue

    return {
        "prom_goles": round(statistics.mean(goles), 2) if goles else 0,
        "prom_tiros": round(statistics.mean(tiros), 1) if tiros else "N/A",
        "prom_posesion": round(statistics.mean(posesion), 1) if posesion else "N/A"
    }

def predecir_marcador(gl_home, gl_away):
    return round(gl_home * 1.15), round(gl_away * 0.95)

def elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts):
    if goles_local > goles_away and cuotas_ml:
        return f"🎯 Pick sugerido: Gana {p['local']} @ {cuotas_ml[0]['odd']}"
    elif goles_local < goles_away and cuotas_ml:
        return f"🎯 Pick sugerido: Gana {p['visitante']} @ {cuotas_ml[2]['odd']}"
    elif goles_local == goles_away and cuotas_ml:
        return f"🎯 Pick sugerido: Empate @ {cuotas_ml[1]['odd']}"
    elif goles_local + goles_away >= 3 and cuota_over != "❌":
        return f"🎯 Pick sugerido: Over 2.5 goles @ {cuota_over}"
    elif goles_local >= 1 and goles_away >= 1 and cuota_btts != "❌":
        return f"🎯 Pick sugerido: Ambos anotan (BTTS) @ {cuota_btts}"
    else:
        return "🎯 Pick sugerido: ❌ Sin valor claro en el mercado"

if __name__ == "__main__":
    partidos = obtener_partidos_hoy()
    for p in partidos:
        cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)
        cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)
        cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)

        cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
        cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

        hora_mex, hora_esp = convertir_horas(p["hora_utc"])

        stats_local = obtener_estadisticas_equipo(p["home_id"])
        stats_away = obtener_estadisticas_equipo(p["away_id"])

        goles_local, goles_away = predecir_marcador(stats_local["prom_goles"], stats_away["prom_goles"])

        print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]}')
        print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')
        print(f'Cuotas: 🏠 {cuotas_ml[0]["odd"] if cuotas_ml else "❌"} | 🤝 {cuotas_ml[1]["odd"] if len(cuotas_ml)>1 else "❌"} | 🛫 {cuotas_ml[2]["odd"] if len(cuotas_ml)>2 else "❌"}')
        print(f'Over 2.5: {cuota_over} | BTTS: {cuota_btts}')
        print(f'📊 {p["local"]}: Goles {stats_local["prom_goles"]} | Tiros {stats_local["prom_tiros"]} | Posesión {stats_local["prom_posesion"]}%')
        print(f'📊 {p["visitante"]}: Goles {stats_away["prom_goles"]} | Tiros {stats_away["prom_tiros"]} | Posesión {stats_away["prom_posesion"]}%')
        print(f'🔮 Predicción marcador: {p["local"]} {goles_local} - {goles_away} {p["visitante"]}')
        print(elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts))
        print("-" * 60)
