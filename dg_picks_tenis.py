import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

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
        logging.info(f"Obtenidos {len(partidos)} partidos del día.")
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
        logging.info(f"Obtenidas estadísticas de {len(estadisticas)} partidos.")
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
        return round(prob, 1)
    except:
        return 0.0

# Mostrar picks de rompimiento por estimación estadística

def main():
    partidos = obtener_partidos()
    estadisticas = obtener_estadisticas_rompimiento()

    print("\n🎾 ESTIMACIÓN DE ROMPIMIENTOS EN PRIMER SET (por estadísticas globales):\n")

    if not partidos:
        print("❌ No se encontraron partidos disponibles.")
        return

    for p in partidos:
        match_id = p["match_id"]
        j1 = p["jugador1"]
        j2 = p["jugador2"]
        j1_name = formatear_nombre(j1["name"])
        j2_name = formatear_nombre(j2["name"])

        stats_match = estadisticas.get(match_id, {})
        stats_j1 = stats_match.get(j1["id"], {})
        stats_j2 = stats_match.get(j2["id"], {})

        p1 = evaluar_rompimiento_con_stats(j1, stats_j1)
        p2 = evaluar_rompimiento_con_stats(j2, stats_j2)

        print(f"- {j1_name} vs {j2_name} | 🏟️ {p['torneo']} | 🕒 {p['hora']} | 📅 {p['fecha']}")
        print(f"  🔍 {j1_name}: prob. de rompimiento estimada → {p1}%")
        print(f"  🔍 {j2_name}: prob. de rompimiento estimada → {p2}%")

        if p1 >= 60 and p2 < 50:
            print(f"  ✅ PICK: {j1_name} rompe servicio en 1er set\n")
        elif p2 >= 60 and p1 < 50:
            print(f"  ✅ PICK: {j2_name} rompe servicio en 1er set\n")
        elif p1 >= 60 and p2 >= 60:
            print(f"  ⚠️ PICK: Ambos jugadores pueden romper en 1er set\n")
        else:
            print("  ❌ No se recomienda pick para rompimiento en este partido\n")

if __name__ == "__main__":
    main()
