import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

LIGAS_VALIDAS_IDS = [
    2, 3, 9, 11, 13, 16, 39, 40, 45, 61, 62, 71, 72, 73, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143,
    144, 162, 164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239,
    242, 244, 253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_fixtures():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    partidos = []
    for item in data["response"]:
        liga_id = item["league"]["id"]
        if liga_id not in LIGAS_VALIDAS_IDS:
            continue
        partidos.append({
            "fixture_id": item["fixture"]["id"],
            "liga": item["league"]["name"],
            "local": item["teams"]["home"]["name"],
            "visitante": item["teams"]["away"]["name"]
        })
    return partidos

def obtener_estadisticas(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS)
    data = res.json().get("response", [])
    if not data:
        return None
    try:
        bets = data[0]["bookmakers"][0]["bets"]
        cuotas = {"ML_local": "-", "ML_empate": "-", "ML_visitante": "-", "over_2.5": "-", "btts": "-"}
        for b in bets:
            if b["name"] == "Match Winner":
                for o in b["values"]:
                    if o["value"] == "Home":
                        cuotas["ML_local"] = o["odd"]
                    elif o["value"] == "Draw":
                        cuotas["ML_empate"] = o["odd"]
                    elif o["value"] == "Away":
                        cuotas["ML_visitante"] = o["odd"]
            elif b["name"] == "Over/Under 2.5 goals":
                for o in b["values"]:
                    if o["value"] == "Over 2.5":
                        cuotas["over_2.5"] = o["odd"]
            elif b["name"] == "Both Teams To Score":
                for o in b["values"]:
                    if o["value"] == "Yes":
                        cuotas["btts"] = o["odd"]
        return cuotas
    except:
        return None

def analizar_partido(partido):
    fixture_id = partido["fixture_id"]
    local = partido["local"]
    visitante = partido["visitante"]
    liga = partido["liga"]

    stats = obtener_estadisticas(fixture_id)
    cuotas = obtener_cuotas(fixture_id)

    gf_local = 0
    gf_visitante = 0
    for team_stats in stats:
        if team_stats["team"]["name"] == local:
            for item in team_stats["statistics"]:
                if item["type"] == "Goals For":
                    gf_local = float(item["value"] if item["value"] is not None else 0)
        if team_stats["team"]["name"] == visitante:
            for item in team_stats["statistics"]:
                if item["type"] == "Goals For":
                    gf_visitante = float(item["value"] if item["value"] is not None else 0)

    marcador_tentativo = f"{round(gf_local)} - {round(gf_visitante)}"

    recomendacion_ml = ""
    if gf_local > gf_visitante:
        recomendacion_ml = "Gana Local"
    elif gf_visitante > gf_local:
        recomendacion_ml = "Gana Visitante"
    else:
        recomendacion_ml = "Empate probable"

    recomendacion_ou = ""
    if gf_local + gf_visitante >= 2.8:
        recomendacion_ou = "Over 2.5"

    recomendacion_btts = ""
    if gf_local >= 1 and gf_visitante >= 1:
        recomendacion_btts = "BTTS (Ambos anotan)"

    print(f"\n⚽ {local} vs {visitante} ({liga})")
    print(f"📊 ML: {recomendacion_ml} | BTTS: {recomendacion_btts or '--'} | Over 2.5: {recomendacion_ou or '--'}")
    print(f"📈 Marcador tentativo: {marcador_tentativo}")
    print(f"💸 Cuotas ML: Local {cuotas.get('ML_local', '-')}, Empate {cuotas.get('ML_empate', '-')}, Visitante {cuotas.get('ML_visitante', '-')} | Over 2.5: {cuotas.get('over_2.5', '-')} | BTTS Sí: {cuotas.get('btts', '-')}\n")

def main():
    print(f"🔍 Análisis de partidos del día {FECHA_HOY}")
    partidos = obtener_fixtures()
    print(f"📌 Total partidos encontrados: {len(partidos)}")
    for partido in partidos:
        analizar_partido(partido)

if __name__ == "__main__":
    main()
