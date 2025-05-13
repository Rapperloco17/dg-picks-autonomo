import json
import os
from datetime import datetime
from collections import defaultdict

# Ruta de resultados por liga
RUTA_RESULTADOS = "historial"

# Obtener todos los archivos de resultados
def cargar_resultados():
    resultados = []
    for archivo in os.listdir(RUTA_RESULTADOS):
        if archivo.endswith(".json") and archivo.startswith("resultados_"):
            with open(os.path.join(RUTA_RESULTADOS, archivo), encoding="utf-8") as f:
                datos = json.load(f)
                resultados.extend(datos)
    return resultados

# Calcular estadísticas por equipo
def calcular_estadisticas(resultados):
    equipos = defaultdict(lambda: {
        "partidos": 0, "goles_favor": 0, "goles_contra": 0,
        "btts": 0, "over_2_5": 0, "over_3_5": 0,
        "ultimos_resultados": []
    })

    for partido in resultados:
        home = partido['equipo_local']
        away = partido['equipo_visitante']
        gh = partido['goles_local']
        ga = partido['goles_visitante']

        for equipo, gf, gc, marcador in [(home, gh, ga, 'L'), (away, ga, gh, 'V')]:
            stats = equipos[equipo]
            stats['partidos'] += 1
            stats['goles_favor'] += gf
            stats['goles_contra'] += gc
            if gf > 0 and gc > 0:
                stats['btts'] += 1
            if gf + gc >= 2.5:
                stats['over_2_5'] += 1
            if gf + gc >= 3.5:
                stats['over_3_5'] += 1

        # Resultado para forma
        if gh > ga:
            equipos[home]['ultimos_resultados'].append('W')
            equipos[away]['ultimos_resultados'].append('L')
        elif gh < ga:
            equipos[home]['ultimos_resultados'].append('L')
            equipos[away]['ultimos_resultados'].append('W')
        else:
            equipos[home]['ultimos_resultados'].append('D')
            equipos[away]['ultimos_resultados'].append('D')

    return equipos

def obtener_stats_equipo(equipos, nombre):
    stats = equipos.get(nombre)
    if not stats:
        return None
    p = stats['partidos'] if stats['partidos'] > 0 else 1
    return {
        'GF': stats['goles_favor'] / p,
        'GC': stats['goles_contra'] / p,
        '%BTTS': (stats['btts'] / p) * 100,
        '%Over2.5': (stats['over_2_5'] / p) * 100,
        '%Over3.5': (stats['over_3_5'] / p) * 100,
        'Forma': ''.join(stats['ultimos_resultados'][-5:])
    }

# Estimación lógica de resultado
def estimar_partido(local, visitante, equipos):
    s1 = obtener_stats_equipo(equipos, local)
    s2 = obtener_stats_equipo(equipos, visitante)
    if not s1 or not s2:
        return None

    marcador = (round((s1['GF'] + s2['GC']) / 2), round((s2['GF'] + s1['GC']) / 2))
    pick = "Empate"
    doble = "12"
    if marcador[0] > marcador[1]: pick = f"Gana {local}"; doble = "1X"
    elif marcador[1] > marcador[0]: pick = f"Gana {visitante}"; doble = "X2"

    over = "Under 2.5"
    if (s1['GF'] + s2['GF']) / 2 >= 1.8: over = "Over 2.5"
    if (s1['GF'] + s2['GF']) / 2 >= 3.0: over = "Over 3.5"

    return {
        "partido": f"{local} vs {visitante}",
        "Marcador": f"{marcador[0]}-{marcador[1]}",
        "ML": pick,
        "Doble": doble,
        "Goles": over,
        "BTTS%": round((s1['%BTTS'] + s2['%BTTS'])/2,1),
        "Forma L": s1['Forma'],
        "Forma V": s2['Forma']
    }

# --- Simulación de partidos del día (puedes conectar API luego) ---
partidos = [
    ("América", "Pumas UNAM"),
    ("Tigres", "Chivas"),
    ("León", "Toluca")
]

print("\n🔍 Análisis DG Picks")
resultados = cargar_resultados()
equipos = calcular_estadisticas(resultados)

for local, visitante in partidos:
    pred = estimar_partido(local, visitante, equipos)
    if pred:
        print(f"\n📊 {pred['partido']}")
        print(f"   Marcador Estimado: {pred['Marcador']}")
        print(f"   ML: {pred['ML']} | Doble: {pred['Doble']} | Línea: {pred['Goles']}")
        print(f"   Forma: {local}: {pred['Forma L']} | {visitante}: {pred['Forma V']}")
        print(f"   BTTS estimado: {pred['BTTS%']}%")
    else:
        print(f"\n⚠️ No hay datos suficientes para {local} vs {visitante}")
