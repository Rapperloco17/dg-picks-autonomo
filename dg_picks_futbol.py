import json
import os
import datetime
import requests
from utils.prediccion_resultado import predecir_resultado
from utils.cuotas import obtener_cuota_fixture

hoy = datetime.date.today().strftime("%Y-%m-%d")

# Diccionario con los ID reales y nombres de archivo correctos
ligas_dict = {
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
    135: "serie_a_italia",
    136: "serie_b_italia",
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
    207: "super_league_suiza",
    210: "hnl",
    218: "bundesliga_austria",
    239: "primera_a_colombia",
    242: "liga_pro",
    244: "veikkausliiga",
    253: "mls",
    257: "us_open_cup",
    262: "liga_mx",
    263: "liga_expansion_mx",
    265: "primera_division_chile",
    268: "primera_division_apertura",
    271: "nb_i",
    281: "primera_division_venezuela",
    345: "czech_liga",
    357: "premier_division_irlanda"
}

print("\n\U0001F4C5 Partidos válidos en ligas activas con historial:")
partidos_analizados = []

for lid, nombre_archivo in ligas_dict.items():
    ruta = f"historial/unificados/resultados_{nombre_archivo}.json"
    if not os.path.exists(ruta):
        continue

    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    partidos = [p for p in data if p.get("fecha") == hoy]

    if not partidos:
        continue

    print(f"\u2705 {nombre_archivo} (ID: {lid}) - {len(partidos)} partidos")

    for partido in partidos:
        try:
            prediccion = predecir_resultado(partido)
            cuota = obtener_cuota_fixture(partido.get("fixture_id"), mercado="1x2")

            resultado = {
                "liga": nombre_archivo,
                "fixture_id": partido.get("fixture_id"),
                "equipos": f"{partido.get('local')} vs {partido.get('visitante')}",
                "prediccion": prediccion,
                "cuota": cuota,
            }
            partidos_analizados.append(resultado)
        except Exception as e:
            print(f"\u274C Error en partido {partido.get('fixture_id')}: {e}")

if not partidos_analizados:
    print("\u26A0\ufe0f Hoy no hubo partidos válidos con historial para analizar.")
