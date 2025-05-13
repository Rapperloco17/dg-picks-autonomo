# dg_picks_futbol.py (con análisis de resultados históricos integrados)

import json
import os
import pandas as pd
from collections import defaultdict

# === CONFIGURACIÓN ===
DATA_FOLDER = "./resultados"  # Carpeta donde están los archivos resultados_<liga>.json
ULTIMOS_PARTIDOS = 5  # Cuántos partidos considerar por equipo para estadísticas recientes

# === Cargar todos los resultados disponibles ===
def cargar_todos_los_resultados():
    resultados = []
    for archivo in os.listdir(DATA_FOLDER):
        if archivo.endswith(".json") and archivo.startswith("resultados_"):
            with open(os.path.join(DATA_FOLDER, archivo), encoding="utf-8") as f:
                datos = json.load(f)
                resultados.extend(datos)
    return resultados

# === Generar estadísticas por equipo ===
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

# === Integración en DG Picks ===
def analizar_fixture(fixture_equipo_local, fixture_equipo_visitante, resumen_stats):
    stats_local = resumen_stats.get(fixture_equipo_local, {})
    stats_visitante = resumen_stats.get(fixture_equipo_visitante, {})

    analisis = {
        "equipo_local": fixture_equipo_local,
        "equipo_visitante": fixture_equipo_visitante,
        "local_stats": stats_local,
        "visitante_stats": stats_visitante
    }
    return analisis

# === Ejemplo de uso ===
if __name__ == "__main__":
    resultados = cargar_todos_los_resultados()
    resumen_stats = generar_estadisticas_por_equipo(resultados)

    # Ejemplo: analizar un partido del fixture
    ejemplo = analizar_fixture("Arsenal", "Chelsea", resumen_stats)
    print(json.dumps(ejemplo, indent=2, ensure_ascii=False))

