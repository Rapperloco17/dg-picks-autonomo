import requests
import json
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY") or "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_VALIDAS = {
    1: "resultados_world_cup.json",
    2: "resultados_uefa_champions_league.json",
    3: "resultados_uefa_europa_league.json",
    4: "resultados_euro_championship.json",
    9: "resultados_copa_america.json",
    11: "resultados_conmebol_sudamericana.json",
    13: "resultados_conmebol_libertadores.json",
    16: "resultados_concacaf_champions_league.json",
    39: "resultados_premier_league.json",
    40: "resultados_championship.json",
    61: "resultados_ligue_1.json",
    62: "resultados_ligue_2.json",
    71: "resultados_serie_a.json",
    72: "resultados_serie_b.json",
    73: "resultados_copa_do_brasil.json",
    45: "resultados_fa_cup.json",
    78: "resultados_bundesliga.json",
    79: "resultados_2_bundesliga.json",
    88: "resultados_eredivisie.json",
    94: "resultados_primeira_liga.json",
    103: "resultados_eliteserien.json",
    106: "resultados_ekstraklasa.json",
    113: "resultados_allsvenskan.json",
    119: "resultados_superliga.json",
    128: "resultados_liga_profesional_argentina.json",
    129: "resultados_primera_nacional.json",
    130: "resultados_copa_argentina.json",
    135: "resultados_serie_a_italy.json",
    136: "resultados_serie_b_italy.json",
    137: "resultados_coppa_italia.json",
    140: "resultados_la_liga.json",
    141: "resultados_segunda_división.json",
    143: "resultados_copa_del_rey.json",
    144: "resultados_jupiler_pro_league.json",
    162: "resultados_primera_división_costa_rica.json",
    164: "resultados_urvalsdeild.json",
    169: "resultados_super_league_china.json",
    172: "resultados_first_league.json",
    179: "resultados_premiership.json",
    188: "resultados_a_league.json",
    197: "resultados_super_league_1.json",
    203: "resultados_super_lig.json",
    207: "resultados_super_league_switzerland.json",
    210: "resultados_hnl.json",
    218: "resultados_bundesliga_austria.json",
    239: "resultados_primera_a.json",
    242: "resultados_liga_pro.json",
    244: "resultados_veikkausliiga.json",
    253: "resultados_major_league_soccer.json",
    257: "resultados_us_open_cup.json",
    262: "resultados_liga_mx.json",
    263: "resultados_liga_de_expansión_mx.json",
    265: "resultados_primera_división_chile.json",
    268: "resultados_primera_división_apertura.json",
    271: "resultados_nb_i.json",
    281: "resultados_primera_división_peru.json",
    345: "resultados_czech_liga.json",
    357: "resultados_premier_division_ireland.json"
}


resultados_fichas = []

def obtener_partidos_del_dia():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        data = response.json()
        return [f for f in data.get("response", []) if f["league"]["id"] in LIGAS_VALIDAS]
    except Exception as e:
        print(f"❌ Error al obtener fixtures: {e}")
        return []

def obtener_detalles_fixture(fixture_id):
    try:
        url = f"{BASE_URL}/fixtures?id={fixture_id}&include=predictions,statistics,odds"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json().get("response", [])[0]
    except Exception as e:
        return {"error": str(e), "fixture_id": fixture_id}

def analizar_partido(f):
    fid = f["fixture"]["id"]
    lid = f["league"]["id"]
    local = f["teams"]["home"]["name"]
    visitante = f["teams"]["away"]["name"]
    liga = f["league"]["name"]

    detalle = obtener_detalles_fixture(fid)
    if "error" in detalle:
        print(f"❌ Error al obtener detalles para {fid}: {detalle['error']}")
        return

    pred = detalle.get("predictions", {})
    stats = detalle.get("statistics", [])
    odds = detalle.get("odds", {}).get("betting", [])
    goles_esperados = detalle.get("goals", {})

    tiros_local = tarjetas_local = corners_local = 0
    tiros_visita = tarjetas_visita = corners_visita = 0

    for equipo_stats in stats:
        equipo = equipo_stats.get("team", {}).get("name", "")
        for stat in equipo_stats.get("statistics", []):
            if equipo == local:
                if stat["type"] == "Shots on Goal": tiros_local = stat["value"] or 0
                if stat["type"] == "Total Corners": corners_local = stat["value"] or 0
                if stat["type"] == "Yellow Cards": tarjetas_local += stat["value"] or 0
            elif equipo == visitante:
                if stat["type"] == "Shots on Goal": tiros_visita = stat["value"] or 0
                if stat["type"] == "Total Corners": corners_visita = stat["value"] or 0
                if stat["type"] == "Yellow Cards": tarjetas_visita += stat["value"] or 0

    cuota_local = cuota_empate = cuota_visitante = cuota_over25 = cuota_btts_si = None

    for casa in odds:
        for apuesta in casa.get("bets", []):
            if apuesta["name"] == "Match Winner":
                for v in apuesta["values"]:
                    if v["value"] == "Home": cuota_local = v["odd"]
                    elif v["value"] == "Draw": cuota_empate = v["odd"]
                    elif v["value"] == "Away": cuota_visitante = v["odd"]
            elif apuesta["name"] == "Over/Under 2.5":
                for v in apuesta["values"]:
                    if v["value"] == "Over 2.5": cuota_over25 = v["odd"]
            elif apuesta["name"] == "Both Teams To Score":
                for v in apuesta["values"]:
                    if v["value"] == "Yes": cuota_btts_si = v["odd"]

    sugerido = "Sin sugerencia"
    if goles_esperados.get("home", 0) and goles_esperados.get("away", 0):
        if goles_esperados["home"] > goles_esperados["away"]:
            sugerido = f"Gana {local}"
        elif goles_esperados["home"] < goles_esperados["away"]:
            sugerido = f"Gana {visitante}"
        else:
            sugerido = "Empate"

    resultados_fichas.append({
        "fixture_id": fid,
        "local": local,
        "visitante": visitante,
        "liga": liga,
        "fecha": f["fixture"]["date"][:10],
        "xg_local": goles_esperados.get("home", "-"),
        "xg_visitante": goles_esperados.get("away", "-"),
        "tiros_local": tiros_local,
        "tiros_visitante": tiros_visita,
        "tarjetas_local": tarjetas_local,
        "tarjetas_visitante": tarjetas_visita,
        "corners_local": corners_local,
        "corners_visitante": corners_visita,
        "cuota_local": cuota_local,
        "cuota_empate": cuota_empate,
        "cuota_visitante": cuota_visitante,
        "cuota_over25": cuota_over25,
        "cuota_btts": cuota_btts_si,
        "pick": sugerido,
        "justificacion": "Análisis por xG y ofensiva vs defensiva",
        "cuota_pick": cuota_local if sugerido == f"Gana {local}" else "-"
    })

    print(f"\n✅ {local} vs {visitante} — Pick: {sugerido} — Cuota: {cuota_local if sugerido == f'Gana {local}' else '-'}")

def main():
    print("\n🚀 Cargando fixtures del día...")
    partidos = obtener_partidos_del_dia()
    for f in partidos:
        analizar_partido(f)

    with open("fixture_resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_fichas, f, ensure_ascii=False, indent=2)
        print("\n💾 Archivo fixture_resultados.json guardado con éxito.")

if __name__ == "__main__":
    main()
