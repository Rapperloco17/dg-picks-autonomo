import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

# Configuración inicial
API_KEY = "189a631b589d485730ac08dda125528a"
BASE_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/tennis_scores"
HEADERS = {"User-Agent": "DG Picks Tenis"}

# Usar JSON para facilitar parseo (aunque la estructura original es XML)
JSON_SUFFIX = "?json=1"

# Endpoints
FIXTURES_URL = f"{BASE_URL}/home{JSON_SUFFIX}"
H2H_BASE_URL = f"{BASE_URL}/h2h_"
PROFILE_URL = f"{BASE_URL}/profile?id="
ODDS_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/getodds/soccer?cat=tennis_10&json=1"

# Utilidad para formatear nombre de jugador

def formatear_nombre(nombre):
    return nombre.strip().replace("\n", " ").title()

# Obtener partidos del día

def obtener_partidos():
    try:
        response = requests.get(FIXTURES_URL, headers=HEADERS)
        data = response.json()

        # Validar que data sea un dict y contenga 'scores'
        if not isinstance(data, dict):
            logging.error("Respuesta no es un JSON válido")
            return []

        partidos = []

        for torneo in data.get("scores", []):
            for match in torneo.get("match", []):
                if match["status"] == "Not Started":
                    jugadores = match["player"]
                    partidos.append({
                        "match_id": match["id"],
                        "fecha": match["date"],
                        "hora": match["time"],
                        "torneo": torneo["name"],
                        "jugador1": jugadores[0],
                        "jugador2": jugadores[1]
                    })

        return partidos
    except Exception as e:
        logging.error(f"Error al obtener partidos: {e}")
        return []

# Buscar H2H

def obtener_h2h(id1, id2):
    url = f"{H2H_BASE_URL}{id1}-{id2}{JSON_SUFFIX}"
    try:
        response = requests.get(url, headers=HEADERS)
        return response.json()
    except Exception as e:
        logging.warning(f"No se pudo obtener H2H: {e}")
        return None

# Simular evaluación de probabilidad de rompimiento (placeholder)

def evaluar_rompimiento(jugador):
    # En la versión real se usarán stats como games al resto, puntos ganados, etc.
    nombre = formatear_nombre(jugador["name"])
    probabilidad = 65 if "Zverev" in nombre else 40
    return probabilidad

# Generar pick con lógica base

def generar_pick(partido):
    j1 = partido["jugador1"]
    j2 = partido["jugador2"]
    p1 = evaluar_rompimiento(j1)
    p2 = evaluar_rompimiento(j2)

    if p1 >= 60 and p2 <= 45:
        pick = f"{formatear_nombre(j1['name'])} rompe servicio en el 1er set"
    elif p2 >= 60 and p1 <= 45:
        pick = f"{formatear_nombre(j2['name'])} rompe servicio en el 1er set"
    elif p1 >= 60 and p2 >= 60:
        pick = f"Ambos jugadores rompen servicio en el 1er set"
    else:
        pick = f"{formatear_nombre(j1['name'])} vs {formatear_nombre(j2['name'])} - No hay valor claro"

    return {
        "pick": pick,
        "hora": partido["hora"],
        "torneo": partido["torneo"]
    }

# Mostrar picks

def main():
    partidos = obtener_partidos()
    print("\nPICKS DE TENIS (ROMPIMIENTO 1ER SET):\n")
    for p in partidos:
        resultado = generar_pick(p)
        print(f"🎾 {resultado['pick']}\n🕒 Hora: {resultado['hora']} | 🏟️ {resultado['torneo']}\n")

if __name__ == "__main__":
    main()
