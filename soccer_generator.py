import requests
import json
from datetime import datetime
from utils.soccer_utils import analyze_match, get_soccer_matches
from utils.odds_api import get_odds_for_match
from utils.telegram_sender import send_pick_to_channel

API_FOOTBALL_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"

LEAGUES_WHITELIST_PATH = "leagues_whitelist.json"
MESSAGE_TEMPLATES_PATH = "message_templates.json"
OUTPUT_FOLDER = "outputs/"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def generate_soccer_picks():
    print("Iniciando generación de picks de fútbol...")

    whitelist = load_json(LEAGUES_WHITELIST_PATH)
    message_templates = load_json(MESSAGE_TEMPLATES_PATH)

    matches = get_soccer_matches(API_FOOTBALL_KEY, whitelist)
    print(f"Partidos obtenidos: {len(matches)}")

    picks = []
    combinadas = []

    for match in matches:
        analysis = analyze_match(match, API_FOOTBALL_KEY)
        if analysis['value_pick']:
            odds = get_odds_for_match(match, ODDS_API_KEY)
            if odds:
                pick_data = {
                    "partido": match['teams'],
                    "liga": match['league_name'],
                    "pick": analysis['pick'],
                    "cuota": odds[analysis['pick']],
                    "analisis": analysis['reason']
                }
                picks.append(pick_data)

    # Clasificación de combinadas
    total_cuota = 1
    for pick in picks[:5]:
        total_cuota *= float(pick['cuota'])

    if 50 <= total_cuota < 150:
        nombre = "Parlay Soñador"
        mensaje = message_templates['soñadora']
    elif total_cuota >= 150:
        nombre = "Bomba Legendaria"
        mensaje = message_templates['bomba']
    else:
        nombre = None
        mensaje = None

    if nombre:
        combinadas.append({
            "nombre": nombre,
            "cuota_total": round(total_cuota, 2),
            "picks": picks[:5],
            "mensaje": mensaje
        })

    # Guardado
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = f"{OUTPUT_FOLDER}futbol_{fecha_hoy}.json"
    save_json({"picks": picks, "combinadas": combinadas}, archivo_salida)
    print(f"Guardado en: {archivo_salida}")

    # Opcional: Enviar al canal VIP / Free
    # for pick in picks:
    #     send_pick_to_channel(pick)

if __name__ == "__main__":
    generate_soccer_picks()
# soccer_generator.py - contenido generado automáticamente
