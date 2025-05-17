import json
import os
from datetime import datetime
from api_football import obtener_partidos_hoy, obtener_estadisticas_fixture

# Cargar historial por liga (solo una vez al inicio)
def cargar_historial():
    historial = {}
    carpeta = "historial/unificados"
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".json"):
            liga = archivo.replace("resultados_", "").replace(".json", "")
            with open(os.path.join(carpeta, archivo), encoding="utf-8") as f:
                historial[liga] = json.load(f)
    return historial

# Calcular promedios por equipo
def calcular_stats(equipo, partidos):
    goles_favor, goles_contra, btts, over25 = [], [], [], []
    for p in partidos:
        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")
        goles_local = p.get("goles_local")
        goles_visitante = p.get("goles_visitante")

        if local is None or visitante is None or goles_local is None or goles_visitante is None:
            continue

        if equipo == local or equipo == visitante:
            if equipo == local:
                gf, gc = goles_local, goles_visitante
            else:
                gf, gc = goles_visitante, goles_local

            goles_favor.append(gf)
            goles_contra.append(gc)
            btts.append(1 if goles_local > 0 and goles_visitante > 0 else 0)
            over25.append(1 if goles_local + goles_visitante > 2.5 else 0)

    total = len(goles_favor)
    if total == 0:
        return {"juegos": 0, "goles_favor": 0, "goles_contra": 0, "btts_pct": 0, "over25_pct": 0}

    return {
        "juegos": total,
        "goles_favor": sum(goles_favor) / total,
        "goles_contra": sum(goles_contra) / total,
        "btts_pct": 100 * sum(btts) / total,
        "over25_pct": 100 * sum(over25) / total
    }

# Analizar partido usando historial
def analizar_fixture(fixture, historial):
    fixture_id = fixture['fixture']['id']
    liga_id = fixture['league']['id']
    fecha = fixture['fixture']['date'][:10]
    nombre_liga = fixture['league']['name']

    equipo_local = fixture['teams']['home']['name']
    equipo_visitante = fixture['teams']['away']['name']

    print(f"\n\U0001F4C4 Analizando: {equipo_local} vs {equipo_visitante} (Fixture ID: {fixture_id})")

    # Buscar historial por liga
    partidos_liga = historial.get(str(liga_id)) or historial.get(nombre_liga.lower().replace(" ", "_"))
    if not partidos_liga:
        print("\u274C No se encontró historial para esta liga")
        return

    # Calcular stats
    stats_local = calcular_stats(equipo_local, partidos_liga)
    stats_visitante = calcular_stats(equipo_visitante, partidos_liga)

    print("  \U0001F4CA Stats Local:", stats_local)
    print("  \U0001F4CA Stats Visitante:", stats_visitante)

    # Condiciones para sugerir pick
    if stats_local['btts_pct'] > 60 and stats_visitante['btts_pct'] > 50:
        print(f"\u2705 Pick sugerido: Ambos Anotan (valor detectado)")
    elif stats_local['over25_pct'] > 60 and stats_visitante['over25_pct'] > 60:
        print(f"\u2705 Pick sugerido: Over 2.5 goles (valor detectado)")
    else:
        print(f"\u274C No hay suficiente respaldo estadístico para un pick.")

# MAIN
if __name__ == "__main__":
    fixtures = obtener_partidos_hoy()
    historial = cargar_historial()

    for fixture in fixtures:
        analizar_fixture(fixture, historial)
