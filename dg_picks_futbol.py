
import requests
import os
from datetime import datetime
import pytz

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
                "id_fixture": fixture["fixture"]["id"]
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

if __name__ == "__main__":
    partidos = obtener_partidos_hoy()
    for p in partidos:
        cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)  # ML
        cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)  # Over/Under
        cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)  # BTTS

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
        print("-" * 60)
