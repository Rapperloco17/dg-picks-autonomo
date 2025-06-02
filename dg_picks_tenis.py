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
P2P_URL = f"{BASE_URL}/home_p2p"

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

# Obtener historial punto a punto

def obtener_ultimos_rompimientos():
    try:
        response = requests.get(P2P_URL, headers=HEADERS)
        root = ET.fromstring(response.content)
        historial = {}

        for match in root.findall("match"):
            match_id = match.get("id")
            sets = match.findall("set")
            if not sets:
                continue
            primer_set = sets[0]
            juegos = primer_set.findall("game")
            resumen = {"jugador1": 0, "jugador2": 0}

            for game in juegos:
                if game.get("server") == "player1" and game.get("winner") == "player2":
                    resumen["jugador2"] += 1
                elif game.get("server") == "player2" and game.get("winner") == "player1":
                    resumen["jugador1"] += 1

            historial[match_id] = resumen

        return historial
    except Exception as e:
        logging.error(f"Error al obtener p2p: {e}")
        return {}

# Mostrar partidos con análisis de rompimiento en primer set

def main():
    partidos = obtener_partidos()
    rompimientos = obtener_ultimos_rompimientos()

    print("\n🎾 PARTIDOS DE TENIS DISPONIBLES HOY (ROMPIMIENTO 1ER SET):\n")

    if not partidos:
        print("❌ No se encontraron partidos disponibles.")
        return

    for p in partidos:
        match_id = p["match_id"]
        j1 = formatear_nombre(p["jugador1"]["name"])
        j2 = formatear_nombre(p["jugador2"]["name"])
        romp = rompimientos.get(match_id, {"jugador1": 0, "jugador2": 0})

        r1 = romp.get("jugador1", 0)
        r2 = romp.get("jugador2", 0)

        print(f"- {j1} vs {j2} | 🏟️ {p['torneo']} | 🕒 {p['hora']} | 📅 {p['fecha']}")
        print(f"  🔎 {j1} - Rompimientos 1er set: {r1}")
        print(f"  🔎 {j2} - Rompimientos 1er set: {r2}\n")

if __name__ == "__main__":
    main()
