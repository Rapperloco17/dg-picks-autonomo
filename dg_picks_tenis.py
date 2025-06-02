import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import json

# Configuración inicial
API_KEY = "189a631b589d485730ac08dda125528a"
BASE_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/tennis_scores"
HEADERS = {"User-Agent": "DG Picks Tenis"}

# Endpoints
FIXTURES_URL = f"{BASE_URL}/home"
STATS_URL = f"{BASE_URL}/home_gamestats"

# Utilidad para formatear nombre de jugador

def formatear_nombre(nombre):
    return nombre.strip().replace("\n", " ").title()

# Obtener partidos del día desde XML

def obtener_partidos():
    try:
        response = requests.get(FIXTURES_URL, headers=HEADERS)
        root = ET.fromstring(response.content)
        partidos = []
        for category in root.findall("category"):
            torneo = category.get("name")
            for match in category.findall("match"):
                if match.get("status") == "Not Started":
                    players = match.findall("player")
                    if len(players) == 2:
                        partidos.append({
                            "match_id": match.get("id"),
                            "fecha": match.get("date"),
                            "hora": match.get("time"),
                            "torneo": torneo,
                            "jugador1": {"id": players[0].get("id"), "name": players[0].get("name")},
                            "jugador2": {"id": players[1].get("id"), "name": players[1].get("name")}
                        })
        return partidos
    except Exception as e:
        logging.error(f"Error al obtener partidos: {e}")
        return []

# Obtener estadísticas de rompimiento por match_id

def obtener_estadisticas_rompimiento():
    try:
        response = requests.get(STATS_URL, headers=HEADERS)
        root = ET.fromstring(response.content)
        estadisticas = {}

        for category in root.findall("category"):
            for match in category.findall("match"):
                match_id = match.get("id")
                jugadores = match.findall("player")
                stats = {}

                for player in jugadores:
                    player_id = player.get("id")
                    stat_block = {}
                    for stat in player:
                        stat_block[stat.tag.lower()] = stat.text
                    stats[player_id] = stat_block

                estadisticas[match_id] = stats
        return estadisticas
    except Exception as e:
        logging.error(f"Error al obtener estadísticas: {e}")
        return {}

# Evaluar probabilidad de rompimiento con stats reales

def evaluar_rompimiento_con_stats(jugador, stats):
    try:
        break_points = float(stats.get("breakpointsconverted", "0").replace("%", "").strip())
        return_points = float(stats.get("returnpointswon", "0").replace("%", "").strip())
        prob = (break_points + return_points) / 2
        return round(prob, 2)
    except:
        return 0.0

# Mostrar partidos con estimación de rompimiento

def main():
    partidos = obtener_partidos()
    estadisticas = obtener_estadisticas_rompimiento()

    print("\n🎾 PARTIDOS DE TENIS DISPONIBLES HOY (CON ESTIMACIÓN DE ROMPIMIENTO):\n")

    if not partidos:
        print("❌ No se encontraron partidos disponibles.")
        return

    for p in partidos:
        match_id = p["match_id"]
        j1 = p['jugador1']
        j2 = p['jugador2']
        stats_match = estadisticas.get(match_id, {})

        stats_j1 = stats_match.get(j1["id"], {})
        stats_j2 = stats_match.get(j2["id"], {})

        prob1 = evaluar_rompimiento_con_stats(j1, stats_j1)
        prob2 = evaluar_rompimiento_con_stats(j2, stats_j2)

        j1_name = formatear_nombre(j1["name"])
        j2_name = formatear_nombre(j2["name"])

        print(f"- {j1_name} vs {j2_name} | 🏟️ {p['torneo']} | 🕒 {p['hora']} | 📅 {p['fecha']}")
        print(f"  🔎 {j1_name} - Rompimiento estimado: {prob1}%")
        print(f"  🔎 {j2_name} - Rompimiento estimado: {prob2}%\n")

if __name__ == "__main__":
    main()
