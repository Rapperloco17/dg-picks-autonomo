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
P2P_BASE_URL = f"{BASE_URL}/d-"

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

# Analizar historial de rompimientos en 1er set para un jugador en 20 partidos

def analizar_historial_rompimientos(jugador_id):
    partidos_analizados = 0
    rompimientos = 0

    try:
        for i in range(1, 21):
            url = f"{P2P_BASE_URL}{i}_p2p"
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                continue
            root = ET.fromstring(response.content)

            for match in root.findall("match"):
                players = match.findall("player")
                if len(players) != 2:
                    continue

                id1 = players[0].get("id")
                id2 = players[1].get("id")

                if jugador_id != id1 and jugador_id != id2:
                    continue

                posicion = "player1" if jugador_id == id1 else "player2"
                rival = "player2" if posicion == "player1" else "player1"

                sets = match.findall("set")
                if not sets:
                    continue
                primer_set = sets[0]
                juegos = primer_set.findall("game")

                for game in juegos:
                    if game.get("server") == rival and game.get("winner") == posicion:
                        rompimientos += 1
                        break

                partidos_analizados += 1
                if partidos_analizados >= 20:
                    break

    except Exception as e:
        logging.error(f"Error al analizar historial de rompimientos: {e}")

    porcentaje = round((rompimientos / partidos_analizados) * 100, 2) if partidos_analizados else 0.0
    return partidos_analizados, rompimientos, porcentaje

# Mostrar partidos con análisis de historial de rompimiento en primer set

def main():
    partidos = obtener_partidos()
    print("\n🎾 HISTORIAL DE ROMPIMIENTOS EN PRIMER SET (últimos 20 partidos):\n")

    if not partidos:
        print("❌ No se encontraron partidos disponibles.")
        return

    for p in partidos:
        j1 = p["jugador1"]
        j2 = p["jugador2"]
        j1_name = formatear_nombre(j1["name"])
        j2_name = formatear_nombre(j2["name"])

        print(f"- {j1_name} vs {j2_name} | 🏟️ {p['torneo']} | 🕒 {p['hora']} | 📅 {p['fecha']}")

        t1, r1, pct1 = analizar_historial_rompimientos(j1["id"])
        t2, r2, pct2 = analizar_historial_rompimientos(j2["id"])

        print(f"  🔍 {j1_name}: {r1}/{t1} partidos con rompimiento (1er set) → {pct1}%")
        print(f"  🔍 {j2_name}: {r2}/{t2} partidos con rompimiento (1er set) → {pct2}%\n")

if __name__ == "__main__":
    main()
