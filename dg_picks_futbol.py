import os
import json
from datetime import datetime

# Ruta base de los archivos unificados
BASE_DIR = "historial/unificados"

# Diccionario de ligas con sus IDs y nombres correctos
ligas_autorizadas = {
    1: "world_cup",
    2: "uefa_champions_league",
    3: "uefa_europa_league",
    4: "euro_championship",
    9: "copa_america",
    11: "conmebol_sudamericana",
    13: "conmebol_libertadores",
    16: "concacaf_champions_league",
    39: "premier_league",
    40: "championship",
    45: "fa_cup",
    61: "ligue_1",
    62: "ligue_2",
    71: "serie_a",
    72: "serie_b",
    73: "copa_do_brasil",
    78: "bundesliga",
    79: "2_bundesliga",
    88: "eredivisie",
    94: "primeira_liga",
    103: "eliteserien",
    106: "ekstraklasa",
    113: "allsvenskan",
    119: "superliga",
    128: "liga_profesional_argentina",
    129: "primera_nacional",
    130: "copa_argentina",
    135: "serie_a",
    136: "serie_b",
    137: "coppa_italia",
    140: "la_liga",
    141: "segunda_division",
    143: "copa_del_rey",
    144: "jupiler_pro_league",
    162: "primera_division",
    164: "urvalsdeild",
    169: "super_league",
    172: "first_league",
    179: "premiership",
    188: "a_league",
    197: "super_league_1",
    203: "super_lig",
    207: "super_league",
    210: "hnl",
    218: "bundesliga",
    239: "primera_a",
    242: "liga_pro",
    244: "veikkausliiga",
    253: "major_league_soccer",
    257: "us_open_cup",
    262: "liga_mx",
    263: "liga_de_expansion_mx",
    265: "primera_division",
    268: "primera_division_-_apertura",
    271: "nb_i",
    281: "primera_division",
    345: "czech_liga",
    357: "premier_division"
}

def cargar_resultados(liga_nombre):
    archivo = f"{BASE_DIR}/resultados_{liga_nombre}.json"
    if not os.path.exists(archivo):
        print(f"⚠️ Archivo no encontrado: {archivo}")
        return []
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)

def calcular_stats(equipo, partidos):
    goles_favor, goles_contra = 0, 0
    partidos_bt, partidos_ov25 = 0, 0
    total = 0
    for p in partidos:
        local = p['equipo_local']
        visitante = p['equipo_visitante']
        gl, gv = p['goles_local'], p['goles_visitante']
        if equipo == local or equipo == visitante:
            es_local = equipo == local
            gf = gl if es_local else gv
            gc = gv if es_local else gl
            goles_favor += gf
            goles_contra += gc
            if gl > 0 and gv > 0:
                partidos_bt += 1
            if gl + gv > 2.5:
                partidos_ov25 += 1
            total += 1
    if total == 0:
        return None
    return {
        "juegos": total,
        "goles_favor": round(goles_favor / total, 2),
        "goles_contra": round(goles_contra / total, 2),
        "btts_pct": round(100 * partidos_bt / total, 1),
        "over25_pct": round(100 * partidos_ov25 / total, 1)
    }

def analizar_fixture(fixture_id, equipo_local, equipo_visitante, liga_id):
    liga_nombre = ligas_autorizadas.get(liga_id)
    if not liga_nombre:
        print(f"⚠️ Liga no reconocida: ID {liga_id}")
        return
    partidos = cargar_resultados(liga_nombre)
    stats_local = calcular_stats(equipo_local, partidos)
    stats_visitante = calcular_stats(equipo_visitante, partidos)

    print(f"\n📊 Analizando fixture {fixture_id}...")
    if not stats_local or not stats_visitante:
        print("⚠️ No hay suficientes datos para analizar el partido.")
        return

    print(f"📌 Stats Local: {stats_local}")
    print(f"📌 Stats Visitante: {stats_visitante}")

    if stats_local['btts_pct'] > 60 and stats_visitante['btts_pct'] > 50:
        print("✅ Pick sugerido: Ambos Anotan (valor detectado)")
    elif stats_local['over25_pct'] > 60 and stats_visitante['over25_pct'] > 55:
        print("✅ Pick sugerido: Over 2.5 goles (valor detectado)")
    else:
        print("⚠️ No hay suficiente respaldo estadístico para un pick.")

# 🧪 EJEMPLO DE PRUEBA
analizar_fixture(
    fixture_id=123456,
    equipo_local="Villarreal",
    equipo_visitante="Leganes",
    liga_id=140
)

