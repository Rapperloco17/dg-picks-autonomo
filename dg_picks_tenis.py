import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import json
import re

# Configuración inicial
API_KEY = "189a631b589d485730ac08dda125528a"
BASE_URL = "http://www.goalserve.com/getfeed"
HEADERS = {"User-Agent": "DG Picks Tenis"}

# Parámetros
JSON_SUFFIX = "?json=1"

# Endpoints
D1_URL = f"{BASE_URL}/d1{JSON_SUFFIX}"
HOME_URL = f"{BASE_URL}/home{JSON_SUFFIX}"
ATP_URL = f"{BASE_URL}/atp_tournaments{JSON_SUFFIX}"
H2H_BASE_URL = f"{BASE_URL}/h2h_"
PROFILE_URL = f"{BASE_URL}/profile"
ODDS_URL = f"{BASE_URL}/getodds?cat=tennis_10{JSON_SUFFIX}"

# Utilidad para formatear nombre de jugador
def formatear_nombre(nombre):
    return nombre.strip().replace("\n", " ").title()

# Limpieza de texto para evitar entidades no definidas
def clean_xml_text(text):
    return re.sub(r"&nbsp;", " ", text) if text else text

# Obtener partidos del día (detecta JSON o XML)
def obtener_partidos():
    try:
        endpoints = [
            (D1_URL, "d1"),
            (HOME_URL, "home"),
            (ATP_URL, "atp_tournaments")
        ]
        for url, endpoint_name in endpoints:
            params = {"key": API_KEY}
            response = requests.get(url, headers=HEADERS, params=params)
            content_type = response.headers.get("Content-Type", "")
            data = None

            if response.status_code != 200:
                logging.warning(f"Error {response.status_code} en {endpoint_name}: {response.text}")
                continue

            if "application/json" in content_type:
                data = response.json()
            else:
                try:
                    data = json.loads(response.text)
                except json.JSONDecodeError:
                    logging.warning(f"Respuesta no es JSON en {endpoint_name}. Probando como XML...")
                    # Limpiar texto antes de parsear
                    cleaned_content = clean_xml_text(response.text)
                    try:
                        root = ET.fromstring(cleaned_content.encode('utf-8') if isinstance(cleaned_content, str) else cleaned_content)
                        partidos = []
                        for category in root.findall(".//category"):
                            torneo = category.get("name", "Torneo desconocido")
                            for match in category.findall(".//match"):
                                if match.get("status") == "Not Started":
                                    players = match.findall(".//player")
                                    if len(players) == 2:
                                        partidos.append({
                                            "match_id": match.get("id"),
                                            "fecha": match.get("date"),
                                            "hora": match.get("time"),
                                            "torneo": torneo,
                                            "jugador1": {"name": players[0].get("name")},
                                            "jugador2": {"name": players[1].get("name")}
                                        })
                        if partidos:
                            return partidos
                    except ET.ParseError as e:
                        logging.error(f"Error al parsear XML en {endpoint_name}: {e}")
                        continue

            if not data or not isinstance(data, dict):
                logging.error(f"La respuesta de {endpoint_name} no es un JSON válido (dict)")
                continue

            partidos = []
            scores = data.get("scores", {})
            if isinstance(scores, dict):
                categories = scores.get("category", [])
                if not isinstance(categories, list):
                    categories = [categories]
                for category in categories:
                    torneo = category.get("@name", "Torneo desconocido")
                    matches = category.get("match", [])
                    if not isinstance(matches, list):
                        matches = [matches]
                    for match in matches:
                        if match.get("@status") == "Not Started":
                            players = match.get("player", [])
                            if isinstance(players, list) and len(players) == 2:
                                partidos.append({
                                    "match_id": match.get("@id"),
                                    "fecha": match.get("@date"),
                                    "hora": match.get("@time"),
                                    "torneo": torneo,
                                    "jugador1": {"name": players[0].get("@name")},
                                    "jugador2": {"name": players[1].get("@name")}
                                })
            if partidos:
                return partidos

        logging.error("No se obtuvieron partidos de ningún endpoint.")
        return []

    except Exception as e:
        logging.error(f"Error al obtener partidos: {e}")
        return []

# Buscar H2H
def obtener_h2h(id1, id2):
    url = f"{H2H_BASE_URL}{id1}-{id2}{JSON_SUFFIX}"
    try:
        response = requests.get(url, headers=HEADERS, params={"key": API_KEY})
        return response.json()
    except Exception as e:
        logging.warning(f"No se pudo obtener H2H para {id1}-{id2}: {e}")
        return None

# Simular evaluación de probabilidad de rompimiento (placeholder)
def evaluar_rompimiento(jugador):
    # Placeholder: en la versión real se usarán stats como return_points_won, first_serve, etc.
    nombre = formatear_nombre(jugador["name"])
    probabilidad = 65 if "Zverev" in nombre else 40  # Ejemplo básico
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
    logging.basicConfig(level=logging.INFO)
    partidos = obtener_partidos()
    if not partidos:
        logging.warning("No se encontraron partidos válidos.")
        return
    print("\nPICKS DE TENIS (ROMPIMIENTO 1ER SET):\n")
    for p in partidos:
        resultado = generar_pick(p)
        print(f"🎾 {resultado['pick']}\n🕒 Hora: {resultado['hora']} | 🏟️ {resultado['torneo']}\n")

if __name__ == "__main__":
    main()
