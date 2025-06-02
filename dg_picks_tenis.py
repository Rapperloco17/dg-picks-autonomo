import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import json

# Configuración inicial
API_KEY = "189a631b589d485730ac08dda125528a"
BASE_URL = "http://www.goalserve.com/getfeed"
ODDS_URL = f"{BASE_URL}/getodds?cat=tennis_10&json=1"
HEADERS = {"User-Agent": "DG Picks Tenis"}

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Utilidad para formatear nombre
def formatear_nombre(nombre):
    return nombre.strip().replace("\n", " ").title()

# Obtener partidos del día
def obtener_partidos():
    try:
        response = requests.get(f"{BASE_URL}/home?key={API_KEY}", headers=HEADERS)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        partidos = []
        for category in root.findall("category"):
            torneo = category.get("name", "Torneo desconocido")
            for match in category.findall("match"):
                if match.get("status") == "Not Started":
                    players = match.findall("player")
                    if len(players) == 2:
                        partidos.append({
                            "match_id": match.get("id"),
                            "fecha": match.get("date"),
                            "hora": match.get("time"),
                            "torneo": torneo,
                            "jugador1": formatear_nombre(players[0].get("name")),
                            "jugador2": formatear_nombre(players[1].get("name"))
                        })
        logging.info(f"Obtenidos {len(partidos)} partidos.")
        return partidos
    except ET.ParseError as e:
        logging.error(f"Error al parsear XML de partidos: {e}")
        return []
    except Exception as e:
        logging.error(f"Error al obtener partidos: {e}")
        return []

# Obtener cuotas ML
def obtener_cuotas_ml():
    try:
        response = requests.get(ODDS_URL, headers=HEADERS, params={"key": API_KEY})
        response.raise_for_status()
        data = response.json()
        cuotas = {}

        for item in data.get("odds", []):
            if item.get("sport") != "Tennis":
                continue
            teams = item.get("teams", [])
            odds = item.get("odds", [])
            if len(teams) != 2 or not odds:
                continue

            team1 = formatear_nombre(teams[0])
            team2 = formatear_nombre(teams[1])

            for mercado in odds:
                if mercado.get("label") == "Match Winner" and len(mercado.get("odds", [])) >= 2:
                    ml1 = float(mercado["odds"][0].get("value", 0))
                    ml2 = float(mercado["odds"][1].get("value", 0))
                    if ml1 > 1.0 and ml2 > 1.0:  # Validar cuotas positivas
                        cuotas[f"{team1} vs {team2}"] = {
                            team1: ml1,
                            team2: ml2
                        }
        logging.info(f"Obtenidas {len(cuotas)} cuotas ML.")
        return cuotas
    except json.JSONDecodeError as e:
        logging.error(f"Error al parsear JSON de cuotas: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error al obtener cuotas ML: {e}")
        return {}

# Seleccionar el mejor pick con valor real
def seleccionar_pick_ml(partidos, cuotas):
    mejor_pick = None
    mejor_valor = 0.0

    for p in partidos:
        clave = f"{p['jugador1']} vs {p['jugador2']}"
        if clave not in cuotas:
            continue

        c1 = cuotas[clave].get(p['jugador1'], 0.0)
        c2 = cuotas[clave].get(p['jugador2'], 0.0)

        if not (1.0 < c1 <= 10.0 and 1.0 < c2 <= 10.0):  # Validar rango de cuotas
            continue

        # Valor inverso para detectar infravalorados
        if 1.50 <= c1 <= 1.90:  # Favorito razonable
            valor = (2.1 - c1) * 1.0
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_pick = {
                    "jugador": p['jugador1'],
                    "cuota": c1,
                    "rival": p['jugador2'],
                    "hora": p['hora'],
                    "torneo": p['torneo']
                }
        elif 2.00 <= c2 <= 2.80:  # Underdog con potencial
            valor = (c2 - 1.8) * 1.1
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_pick = {
                    "jugador": p['jugador2'],
                    "cuota": c2,
                    "rival": p['jugador1'],
                    "hora": p['hora'],
                    "torneo": p['torneo']
                }

    return mejor_pick

# Ejecutar selección y mostrar pick
def main():
    partidos = obtener_partidos()
    cuotas = obtener_cuotas_ml()

    print("\n🎾 PICK DG PICKS - ML (Ganador del partido):\n")

    if not partidos or not cuotas:
        print("❌ No hay partidos o cuotas disponibles para hoy.")
        return

    pick = seleccionar_pick_ml(partidos, cuotas)
    if pick:
        print(f"🎯 {pick['jugador']} gana su partido (ML)")
        print(f"💰 Cuota: {pick['cuota']:.2f}")
        print(f"🆚 Rival: {pick['rival']}")
        print(f"📅 {pick['torneo']} | 🕒 {pick['hora']}")
        print("✅ Valor detectado en la cuota")
    else:
        print("⚠️ No se encontró valor suficiente para recomendar un pick ML hoy.")

if __name__ == "__main__":
    main()
