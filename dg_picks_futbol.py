
import requests
import json
from datetime import datetime
import time

# CONFIGURACIÓN
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
WHITELIST = {"2", "3", "61", "78", "135", "140", "253", "262", "203", "81"}  # Ejemplo

# Telegram
BOT_TOKEN = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"
CHAT_ID = "-1001285733813"  # VIP channel

def obtener_partidos_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures"
    params = {"date": hoy}
    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json()
    return [f for f in data["response"] if str(f["league"]["id"]) in WHITELIST]

def obtener_estadisticas_fixture(fixture_id):
    url = f"{BASE_URL}/predictions"
    res = requests.get(url, headers=HEADERS, params={"fixture": fixture_id})
    data = res.json()
    if data["response"]:
        return data["response"][0]
    return None

def obtener_cuotas_fixture(fixture_id):
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id, "bookmaker": 6}  # 6 = Bet365
    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json()
    cuotas = {}
    for b in data.get("response", []):
        for market in b.get("bets", []):
            name = market["name"].lower()
            for val in market["values"]:
                if "over" in val["value"].lower():
                    cuotas["over"] = float(val["odd"])
                elif "under" in val["value"].lower():
                    cuotas["under"] = float(val["odd"])
                elif val["value"].lower() == "yes":
                    cuotas["btts"] = float(val["odd"])
    return cuotas

def analizar_y_generar_picks(partido):
    fixture_id = partido["fixture"]["id"]
    equipos = f'{partido["teams"]["home"]["name"]} vs {partido["teams"]["away"]["name"]}'
    stats = obtener_estadisticas_fixture(fixture_id)
    cuotas = obtener_cuotas_fixture(fixture_id)
    
    if not stats or not cuotas:
        return None

    goles = stats["teams"]["home"]["last_5"]["goals"]["for"]["total"] + stats["teams"]["away"]["last_5"]["goals"]["for"]["total"]
    pick = None

    if goles >= 6 and cuotas.get("over", 0) >= 1.60:
        pick = f"🔥 {equipos}\nPick: Más de 2.5 goles\nCuota: {cuotas['over']}\n✅ Promedio alto de goles"
    elif stats["predictions"]["both_teams_to_score"]["yes"] >= 65 and cuotas.get("btts", 0) >= 1.70:
        pick = f"⚡ {equipos}\nPick: Ambos anotan (BTTS)\nCuota: {cuotas['btts']}\n✅ Alta probabilidad BTTS"

    return pick

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def main():
    partidos = obtener_partidos_hoy()
    for p in partidos:
        pick = analizar_y_generar_picks(p)
        if pick:
            enviar_telegram(pick)
            print("✅ Enviado:", pick)
            time.sleep(1)

if __name__ == "__main__":
    main()
