import os
import json
import requests
from datetime import datetime
import pytz
from send_telegram import enviar_mensaje

CHAT_ID_VIP = os.getenv("CHAT_ID_VIP")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94, 103,
    106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164, 169,
    172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262, 263, 265,
    268, 271, 281, 345, 357
]


def obtener_partidos_del_dia():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    r = requests.get(url, headers=HEADERS).json()
    return [p for p in r.get("response", []) if p["league"]["id"] in LIGAS_VALIDAS]


def obtener_cuotas_por_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    r = requests.get(url, headers=HEADERS).json()
    for entry in r.get("response", []):
        if entry["bookmaker"]["name"] == "Bet365":
            for m in entry.get("bets", []):
                if m["name"] == "Match Winner":
                    odds = {b["value"]: b["odd"] for b in m["values"]}
                    return (
                        float(odds.get("Home", 0)),
                        float(odds.get("Draw", 0)),
                        float(odds.get("Away", 0))
                    )
    return (0, 0, 0)


def obtener_forma_equipo(nombre_equipo):
    resultados = []
    search_url = f"{BASE_URL}/teams?search={nombre_equipo}"
    search = requests.get(search_url, headers=HEADERS).json()
    if not search["response"]:
        return []
    team_id = search["response"][0]["team"]["id"]
    url = f"{BASE_URL}/fixtures?team={team_id}&season=2024&status=FT"
    partidos = requests.get(url, headers=HEADERS).json().get("response", [])
    for p in partidos:
        resultados.append({
            "local": p["teams"]["home"]["name"],
            "visitante": p["teams"]["away"]["name"],
            "goles_local": p["goals"]["home"],
            "goles_visitante": p["goals"]["away"],
            "fecha": p["fixture"]["date"]
        })
    return sorted(resultados, key=lambda x: x["fecha"], reverse=True)[:10]


def calcular_stats(equipo, historial):
    v, e, d, gf, gc = 0, 0, 0, 0, 0
    for p in historial:
        if p["local"] == equipo:
            g_favor, g_contra = p["goles_local"], p["goles_visitante"]
        else:
            g_favor, g_contra = p["goles_visitante"], p["goles_local"]
        gf += g_favor
        gc += g_contra
        if g_favor > g_contra:
            v += 1
        elif g_favor == g_contra:
            e += 1
        else:
            d += 1
    total = len(historial)
    prom_gf = round(gf / total, 2) if total else 0
    prom_gc = round(gc / total, 2) if total else 0
    return v, e, d, gf, gc, prom_gf, prom_gc


def formatear_hora_local(utc_str):
    dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S%z")
    hora_mx = dt.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M")
    hora_es = dt.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
    return hora_mx, hora_es


def generar_mensaje_fixture(fix):
    local = fix["teams"]["home"]["name"]
    visita = fix["teams"]["away"]["name"]
    liga = fix["league"]["name"]
    fecha = fix["fixture"]["date"]
    fixture_id = fix["fixture"]["id"]
    hora_mx, hora_es = formatear_hora_local(fecha)
    cuota_local, cuota_empate, cuota_visita = obtener_cuotas_por_fixture(fixture_id)
    if not (1.40 <= cuota_local <= 3.50 and 1.40 <= cuota_visita <= 3.50):
        return None

    forma_local = obtener_forma_equipo(local)
    forma_visita = obtener_forma_equipo(visita)
    if not forma_local or not forma_visita:
        return None

    vl, el, dl, gfl, gcl, prom_gfl, prom_gcl = calcular_stats(local, forma_local)
    vv, ev, dv, gfv, gcv, prom_gfv, prom_gcv = calcular_stats(visita, forma_visita)

    score_l = vl * 3 + gfl - gcl
    score_v = vv * 3 + gfv - gcv
    marcador_l = round((prom_gfl + prom_gcv) / 2)
    marcador_v = round((prom_gfv + prom_gcl) / 2)

    if score_l > score_v + 2:
        pick = f"Gana {local} @ {cuota_local}"
    elif score_v > score_l + 2:
        pick = f"Gana {visita} @ {cuota_visita}"
    elif abs(score_l - score_v) <= 1 and 3.0 <= cuota_empate <= 3.6:
        pick = f"Empate @ {cuota_empate}"
    else:
        return None

    return (
        f"📅 {fecha[:10]} | {liga}\n"
        f"⚽ {local} vs {visita}\n"
        f"🕐 Hora del partido:\n🇲🇽 {hora_mx} CDMX\n🇪🇸 {hora_es} España\n"
        f"💸 Cuotas → Local: {cuota_local} | Empate: {cuota_empate} | Visitante: {cuota_visita}\n"
        f"🔮 Marcador estimado: {local} {marcador_l} – {marcador_v} {visita}\n"
        f"🔵 Local: {vl}V {el}E {dl}D | GF: {gfl} GC: {gcl} | Prom: {prom_gfl}-{prom_gcl}\n"
        f"🔴 Visitante: {vv}V {ev}E {dv}D | GF: {gfv} GC: {gcv} | Prom: {prom_gfv}-{prom_gcv}\n"
        f"🧠 Pick sugerido: {pick}\n#DG_PICKS"
    )


def main():
    fixtures = obtener_partidos_del_dia()
    mensajes = []
    for fix in fixtures:
        msg = generar_mensaje_fixture(fix)
        if msg:
            mensajes.append(msg)

    for i, mensaje in enumerate(mensajes):
        enviar_mensaje(mensaje, CHAT_ID_VIP)
        if i < 2:
            enviar_mensaje(mensaje, CHAT_ID_FREE)


if __name__ == "__main__":
    main()
