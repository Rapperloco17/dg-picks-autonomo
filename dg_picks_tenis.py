import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

# Configuración inicial
API_KEY = "189a631b589d485730ac08dda125528a"
BASE_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/tennis_scores"
ODDS_URL = f"http://www.goalserve.com/getfeed/{API_KEY}/getodds/soccer?cat=tennis_10&json=1"
HEADERS = {"User-Agent": "DG Picks Tenis"}

# Utilidad para formatear nombre

def formatear_nombre(nombre):
    return nombre.strip().replace("\n", " ").title()

# Obtener partidos del día

def obtener_partidos():
    try:
        response = requests.get(f"{BASE_URL}/home", headers=HEADERS)
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
                            "jugador1": formatear_nombre(players[0].get("name")),
                            "jugador2": formatear_nombre(players[1].get("name"))
                        })
        return partidos
    except Exception as e:
        logging.error(f"Error al obtener partidos: {e}")
        return []

# Obtener cuotas ML

def obtener_cuotas_ml():
    try:
        response = requests.get(ODDS_URL, headers=HEADERS)
        data = response.json()
        cuotas = {}

        for item in data:
            if item.get("sport") != "Tennis":
                continue

            teams = item.get("teams", [])
            odds = item.get("odds", [])
            if len(teams) != 2 or not odds:
                continue

            team1 = formatear_nombre(teams[0])
            team2 = formatear_nombre(teams[1])

            for mercado in odds:
                if mercado["label"] == "Match Winner" and len(mercado["odds"]):
                    ml1 = float(mercado["odds"][0]["value"])
                    ml2 = float(mercado["odds"][1]["value"])
                    cuotas[f"{team1} vs {team2}"] = {
                        team1: ml1,
                        team2: ml2
                    }
        return cuotas
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

        c1 = cuotas[clave][p['jugador1']]
        c2 = cuotas[clave][p['jugador2']]

        # Valor inverso para detectar infravalorados (cuota más alta con contexto favorable)
        if 1.50 <= c1 <= 1.90:
            valor = (2.1 - c1) * 1.0  # Fuerte favorito razonable
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_pick = {
                    "jugador": p['jugador1'],
                    "cuota": c1,
                    "rival": p['jugador2'],
                    "hora": p['hora'],
                    "torneo": p['torneo']
                }
        elif 2.00 <= c2 <= 2.80:
            valor = (c2 - 1.8) * 1.1  # Underdog con potencial
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
        print(f"💰 Cuota: {pick['cuota']}")
        print(f"🆚 Rival: {pick['rival']}")
        print(f"📅 {pick['torneo']} | 🕒 {pick['hora']}")
        print("✅ Valor detectado en la cuota")
    else:
        print("⚠️ No se encontró valor suficiente para recomendar un pick ML hoy.")

if __name__ == "__main__":
    main()
