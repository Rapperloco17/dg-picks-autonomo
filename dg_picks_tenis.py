import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import json

# Configuración inicial
API_KEY = "189a631b589d485730ac08dda125528a"
BASE_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/tennis_scores"
HEADERS = {"User-Agent": "DG Picks Tenis"}

# Usar solo XML porque JSON falla o no está disponible
FIXTURES_URL = f"{BASE_URL}/home"
H2H_BASE_URL = f"{BASE_URL}/h2h_"
PROFILE_URL = f"{BASE_URL}/profile?id="
ODDS_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/getodds/soccer?cat=tennis_10&json=1"

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
                            "jugador1": {"name": players[0].get("name")},
                            "jugador2": {"name": players[1].get("name")}
                        })
        return partidos

    except Exception as e:
        logging.error(f"Error al obtener partidos: {e}")
        return []

# Mostrar solo partidos (debug)

def main():
    partidos = obtener_partidos()
    print("\n🎾 PARTIDOS DE TENIS DISPONIBLES HOY (RAW):\n")

    if not partidos:
        print("❌ No se encontraron partidos disponibles.")
        return

    for p in partidos:
        j1 = formatear_nombre(p['jugador1']['name'])
        j2 = formatear_nombre(p['jugador2']['name'])
        print(f"- {j1} vs {j2} | 🏟️ {p['torneo']} | 🕒 {p['hora']} | 📅 {p['fecha']}")

if __name__ == "__main__":
    main()
