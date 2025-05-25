
import requests
import json
import os
from datetime import datetime
import pytz
from send_telegram import enviar_mensaje

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_VALIDAS = [140, 39, 78, 61, 94, 88, 203, 128, 11, 13]
CANAL_VIP = "-1001285733813"
CANAL_FREE = "@dgpickspro17"

def obtener_partidos_del_dia():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS).json()
    return [p for p in response.get("response", []) if p["league"]["id"] in LIGAS_VALIDAS]

def buscar_partidos_api(team_name):
    search = requests.get(f"{BASE_URL}/teams?search={team_name}", headers=HEADERS).json()
    team_info = search["response"][0] if search["response"] else None
    if not team_info:
        return []
    team_id = team_info["team"]["id"]
    url = f"{BASE_URL}/fixtures?team={team_id}&season=2024&status=FT"
    r = requests.get(url, headers=HEADERS).json()
    return r.get("response", [])

def cargar_historial_local():
    historial = []
    carpeta = "historial/unificados/"
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".json"):
            with open(os.path.join(carpeta, archivo), "r", encoding="utf-8") as f:
                historial += json.load(f)
    return historial

def obtener_forma_combinada(nombre_equipo, historial):
    local = [p for p in historial if p["equipo_local"] == nombre_equipo or p["equipo_visitante"] == nombre_equipo]

    # Buscar desde API
    api_partidos = buscar_partidos_api(nombre_equipo)
    for partido in api_partidos:
        fix = partido["fixture"]
        teams = partido["teams"]
        goals = partido["goals"]
        historial_format = {
            "fecha": fix["date"][:10],
            "equipo_local": teams["home"]["name"],
            "equipo_visitante": teams["away"]["name"],
            "goles_local": goals["home"],
            "goles_visitante": goals["away"]
        }
        local.append(historial_format)

    # Ordenar y tomar últimos 10
    partidos = sorted(local, key=lambda x: x["fecha"], reverse=True)[:10]
    stats = {"victorias": 0, "empates": 0, "derrotas": 0, "goles_a_favor": 0, "goles_en_contra": 0}

    for p in partidos:
        if p["equipo_local"] == nombre_equipo:
            gf, gc = p["goles_local"], p["goles_visitante"]
        else:
            gf, gc = p["goles_visitante"], p["goles_local"]
        stats["goles_a_favor"] += gf
        stats["goles_en_contra"] += gc
        if gf > gc:
            stats["victorias"] += 1
        elif gf == gc:
            stats["empates"] += 1
        else:
            stats["derrotas"] += 1

    total = len(partidos)
    stats["prom_gf"] = round(stats["goles_a_favor"] / total, 2) if total else 0
    stats["prom_gc"] = round(stats["goles_en_contra"] / total, 2) if total else 0
    return stats

def formatear_hora_local(utc_str):
    utc_dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S%z")
    hora_cdmx = utc_dt.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M")
    hora_esp = utc_dt.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
    return hora_cdmx, hora_esp

def analizar_fixture(fix, historial):
    local = fix["teams"]["home"]["name"]
    visitante = fix["teams"]["away"]["name"]
    liga = fix["league"]["name"]
    fecha = fix["fixture"]["date"]

    odds = fix.get("odds", {}).get("1X2", {}) or {}
    cuota_local = odds.get("1", 0)
    cuota_empate = odds.get("X", 0)
    cuota_visitante = odds.get("2", 0)

    if not (1.4 < cuota_local < 3.5 and 1.4 < cuota_visitante < 3.5):
        return None

    forma_local = obtener_forma_combinada(local, historial)
    forma_visita = obtener_forma_combinada(visitante, historial)

    score_local = forma_local["victorias"] * 3 + forma_local["goles_a_favor"] - forma_local["goles_en_contra"]
    score_visita = forma_visita["victorias"] * 3 + forma_visita["goles_a_favor"] - forma_visita["goles_en_contra"]

    if score_local > score_visita + 2:
        pick = f"Gana {local} @ {cuota_local}"
    elif score_visita > score_local + 2:
        pick = f"Gana {visitante} @ {cuota_visitante}"
    elif abs(score_local - score_visita) <= 1 and 3.0 <= cuota_empate <= 3.6:
        pick = f"Empate @ {cuota_empate}"
    else:
        return None

    gl = round((forma_local["prom_gf"] + forma_visita["prom_gc"]) / 2)
    gv = round((forma_visita["prom_gf"] + forma_local["prom_gc"]) / 2)
    hora_cdmx, hora_esp = formatear_hora_local(fecha)

    texto = (
        f"📅 {fecha[:10]} | {liga}
"
        f"⚽ {local} vs {visitante}
"
        f"🕐 Hora del partido:
🇲🇽 {hora_cdmx} CDMX
🇪🇸 {hora_esp} España
"
        f"💸 Cuotas → Local: {cuota_local} | Empate: {cuota_empate} | Visitante: {cuota_visitante}
"
        f"🧠 Pick sugerido: {pick}
"
        f"🔮 Marcador estimado: {local} {gl} – {gv} {visitante}
"
        f"🔵 Local: {forma_local['victorias']}V {forma_local['empates']}E {forma_local['derrotas']}D | GF: {forma_local['goles_a_favor']} GC: {forma_local['goles_en_contra']} | Prom: {forma_local['prom_gf']}-{forma_local['prom_gc']}
"
        f"🔴 Visitante: {forma_visita['victorias']}V {forma_visita['empates']}E {forma_visita['derrotas']}D | GF: {forma_visita['goles_a_favor']} GC: {forma_visita['goles_en_contra']} | Prom: {forma_visita['prom_gf']}-{forma_visita['prom_gc']}
"
        f"{'-'*40}"
    )
    return texto

def main():
    fixtures = obtener_partidos_del_dia()
    historial_local = cargar_historial_local()

    picks = []
    for f in fixtures:
        resultado = analizar_fixture(f, historial_local)
        if resultado:
            picks.append(resultado)

    for i, mensaje in enumerate(picks):
        enviar_mensaje(mensaje, CANAL_VIP)
        if i < 2:
            enviar_mensaje(mensaje, CANAL_FREE)

if __name__ == "__main__":
    main()
