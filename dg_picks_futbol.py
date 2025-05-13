# dg_picks_futbol.py (integrado con análisis de fixtures y resultados históricos)

import json
import os
import pandas as pd
from collections import defaultdict
import requests

# === CONFIGURACIÓN ===
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"
DATA_FOLDER = "./resultados"
ULTIMOS_PARTIDOS = 5

# === Cargar resultados históricos ===
def cargar_todos_los_resultados():
    resultados = []
    for archivo in os.listdir(DATA_FOLDER):
        if archivo.endswith(".json") and archivo.startswith("resultados_"):
            with open(os.path.join(DATA_FOLDER, archivo), encoding="utf-8") as f:
                datos = json.load(f)
                resultados.extend(datos)
    return resultados

def generar_estadisticas_por_equipo(resultados):
    equipos = defaultdict(list)
    for partido in resultados:
        equipos[partido['local']].append(partido)
        equipos[partido['visitante']].append(partido)

    resumen = {}
    for equipo, partidos in equipos.items():
        recientes = sorted(partidos, key=lambda x: x['fecha'], reverse=True)[:ULTIMOS_PARTIDOS]
        goles_a_favor = sum(p['goles_local'] if p['local'] == equipo else p['goles_visitante'] for p in recientes)
        goles_en_contra = sum(p['goles_visitante'] if p['local'] == equipo else p['goles_local'] for p in recientes)
        btts = sum(p['ambos_anotan'] for p in recientes)
        overs = sum(p['over_2_5'] for p in recientes)
        local_juegos = [p for p in recientes if p['local'] == equipo]
        visitante_juegos = [p for p in recientes if p['visitante'] == equipo]

        resumen[equipo] = {
            "prom_goles": goles_a_favor / len(recientes),
            "prom_goles_recibidos": goles_en_contra / len(recientes),
            "%BTTS": round((btts / len(recientes)) * 100, 1),
            "%Over_2_5": round((overs / len(recientes)) * 100, 1),
            "forma_local": sum(1 if p['resultado'] == 'local' else 0 for p in local_juegos),
            "forma_visitante": sum(1 if p['resultado'] == 'visitante' else 0 for p in visitante_juegos),
            "partidos_analizados": len(recientes)
        }
    return resumen

def analizar_fixture(local, visitante, resumen_stats):
    stats_local = resumen_stats.get(local, {})
    stats_visitante = resumen_stats.get(visitante, {})

    analisis = {
        "equipo_local": local,
        "equipo_visitante": visitante,
        "local_stats": stats_local,
        "visitante_stats": stats_visitante,
        "recomendacion": ""
    }

    if stats_local and stats_visitante:
        if stats_local["%Over_2_5"] > 60 and stats_visitante["%Over_2_5"] > 60:
            analisis["recomendacion"] = "Over 2.5"
        elif stats_local["%BTTS"] > 55 and stats_visitante["%BTTS"] > 55:
            analisis["recomendacion"] = "Ambos anotan"
        elif stats_local["forma_local"] >= 3 and stats_visitante["forma_visitante"] <= 1:
            analisis["recomendacion"] = f"Gana {local}"
        elif stats_local["forma_local"] <= 1 and stats_visitante["forma_visitante"] >= 3:
            analisis["recomendacion"] = f"Gana {visitante}"
        else:
            analisis["recomendacion"] = "Sin valor claro"
    else:
        analisis["recomendacion"] = "Sin datos suficientes"

    return analisis

def obtener_fixtures_hoy():
    url = f"{BASE_URL}/fixtures"
    params = {"date": pd.Timestamp.now().strftime("%Y-%m-%d")}
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    return data.get("response", [])

# === Flujo principal ===
if __name__ == "__main__":
    resultados = cargar_todos_los_resultados()
    resumen_stats = generar_estadisticas_por_equipo(resultados)

    fixtures_hoy = obtener_fixtures_hoy()
    print(f"Partidos hoy: {len(fixtures_hoy)}")

    picks_generados = []
    for f in fixtures_hoy:
        local = f['teams']['home']['name']
        visitante = f['teams']['away']['name']
        analisis = analizar_fixture(local, visitante, resumen_stats)
        picks_generados.append(analisis)

    for pick in picks_generados:
        print(json.dumps(pick, indent=2, ensure_ascii=False))
