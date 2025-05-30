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
    hoy = datetime.now(pytz.utc).strftime("%Y-%m-%d")
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

def obtener_estadisticas_equipo(equipo_id, condicion):
    url = f"{BASE_URL}/fixtures?team={equipo_id}&last=20"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    gf, gc, tiros, posesion = [], [], [], []
    ganados = empatados = perdidos = 0

    for match in data.get("response", []):
        if condicion == "local" and match["teams"]["home"]["id"] != equipo_id:
            continue
        if condicion == "visitante" and match["teams"]["away"]["id"] != equipo_id:
            continue

        try:
            fixture_id = match["fixture"]["id"]
            if match["teams"]["home"]["id"] == equipo_id:
                goles_favor = match["goals"]["home"]
                goles_contra = match["goals"]["away"]
            else:
                goles_favor = match["goals"]["away"]
                goles_contra = match["goals"]["home"]

            gf.append(goles_favor)
            gc.append(goles_contra)

            if goles_favor > goles_contra:
                ganados += 1
            elif goles_favor == goles_contra:
                empatados += 1
            else:
                perdidos += 1

            stats_url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}&team={equipo_id}"
            stats_res = requests.get(stats_url, headers=HEADERS).json()
            if not stats_res.get("response"):
                continue

            stats = stats_res["response"][0].get("statistics", [])
            for stat in stats:
                if stat["type"] == "Shots on Goal" and stat["value"]:
                    tiros.append(int(stat["value"]))
                if stat["type"] == "Ball Possession" and stat["value"]:
                    posesion.append(int(stat["value"].replace("%", "")))
        except:
            continue

    return {
        "gf": round(statistics.mean([x for x in gf if isinstance(x, (int, float))]), 2) if gf else 0,
        "gc": round(statistics.mean([x for x in gc if isinstance(x, (int, float))]), 2) if gc else 0,
        "tiros": round(statistics.mean([x for x in tiros if isinstance(x, (int, float))]), 1) if tiros else "N/A",
        "posesion": round(statistics.mean([x for x in posesion if isinstance(x, (int, float))]), 1) if posesion else "N/A",
        "forma": f"{ganados}G - {empatados}E - {perdidos}P"
    }

def predecir_marcador(local, visitante):
    g_local = round((local["gf"] + visitante["gc"]) / 2 * 1.1)
    g_visit = round((visitante["gf"] + local["gc"]) / 2 * 0.9)
    return g_local, g_visit

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

def evaluar_advertencia(pick, stats_local, stats_away):
    advertencia = ""
    if "Gana" in pick and "Empate" not in pick:
        equipo = pick.split("Gana ")[1].split(" @")[0]
        if equipo in stats_local.get("nombre", ""):
            victorias = int(stats_local["forma"].split("G")[0])
            if victorias < 2:
                advertencia = "⚠️ Ojo: el equipo local no viene en buena forma en casa."
        elif equipo in stats_away.get("nombre", ""):
            victorias = int(stats_away["forma"].split("G")[0])
            if victorias < 2:
                advertencia = "⚠️ Cuidado: el visitante no viene fuerte fuera de casa."
    return advertencia

def calcular_score(stats_local, stats_away, goles_local, goles_away, cuota):
    score = 0
    if abs(goles_local - goles_away) >= 2:
        score += 2
    if stats_local["forma"].startswith("3") or stats_local["forma"].startswith("4") or stats_local["forma"].startswith("5"):
        score += 1
    if isinstance(stats_local["tiros"], (int, float)) and stats_local["tiros"] >= 4:
        score += 1
    if isinstance(stats_local["posesion"], (int, float)) and stats_local["posesion"] >= 55:
        score += 1
    try:
        cuota_valor = float(cuota)
        if 1.55 <= cuota_valor <= 3.50:
            score += 1
    except:
        pass
    return score

def interpretar_score(score):
    if score >= 5:
        return f"💎 PICK DESTACADO (Score: {score}/6)"
    elif score == 4:
        return f"✅ PICK CON VALOR (Score: {score}/6)"
    elif score <= 2:
        return f"⚠️ PICK DUDOSO (Score: {score}/6)"
    else:
        return f"Score: {score}/6"

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
            cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)
            cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)
            cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)

            cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
            cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

            hora_mex, hora_esp = convertir_horas(p["hora_utc"])

            stats_local = obtener_estadisticas_equipo(p["home_id"], "local")
            stats_away = obtener_estadisticas_equipo(p["away_id"], "visitante")
            stats_local["nombre"] = p["local"]
            stats_away["nombre"] = p["visitante"]

            goles_local, goles_away = predecir_marcador(stats_local, stats_away)

            print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]}')
            print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')
            print(f'Cuotas: 🏠 {cuotas_ml[0]["odd"] if cuotas_ml else "❌"} | 🤝 {cuotas_ml[1]["odd"] if len(cuotas_ml)>1 else "❌"} | 🛫 {cuotas_ml[2]["odd"] if len(cuotas_ml)>2 else "❌"}')
            print(f'Over 2.5: {cuota_over} | BTTS: {cuota_btts}')
            print(f'📊 {p["local"]} (Local): GF {stats_local["gf"]} | GC {stats_local["gc"]} | Tiros {stats_local["tiros"]} | Posesión {stats_local["posesion"]}% | Forma: {stats_local["forma"]}')
            print(f'📊 {p["visitante"]} (Visitante): GF {stats_away["gf"]} | GC {stats_away["gc"]} | Tiros {stats_away["tiros"]} | Posesión {stats_away["posesion"]}% | Forma: {stats_away["forma"]}')
            print(f'🔮 Predicción marcador: {p["local"]} {goles_local} - {goles_away} {p["visitante"]}')
            pick = elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts)
            print(pick)
            advertencia = evaluar_advertencia(pick, stats_local, stats_away)
            if advertencia:
                print(advertencia)
            cuota_principal = pick.split("@")[-1].strip() if "@" in pick else "0"
            score = calcular_score(stats_local, stats_away, goles_local, goles_away, cuota_principal)
            print(interpretar_score(score))

            prob_local = calcular_probabilidades_btts_over(p["home_id"], "local")
            prob_away = calcular_probabilidades_btts_over(p["away_id"], "visitante")
            print(f'📊 Probabilidades (últimos 20 partidos):')
            print(f'- {p["local"]}: BTTS {prob_local["btts"]}% | Over 2.5 {prob_local["over"]}%')
            print(f'- {p["visitante"]}: BTTS {prob_away["btts"]}% | Over 2.5 {prob_away["over"]}%')

            print("-" * 60)