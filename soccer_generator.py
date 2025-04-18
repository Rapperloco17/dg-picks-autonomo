import json
import os
from datetime import datetime
from utils.telegram import log_envio
from utils.soccer_stats import analyze_match, get_soccer_matches
from utils.odds_api import get_odds_for_match

API_FOOTBALL_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"

LEAGUES_WHITELIST_PATH = "leagues_whitelist.json"
MESSAGE_TEMPLATES_PATH = "message_templates.json"
OUTPUT_FOLDER = "outputs"


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
        analysis = analyze_match(match)  # Corregido: solo 1 argumento
        if analysis:
            picks.append(analysis)

    fecha = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_FOLDER, f"futbol_{fecha}.json")

    save_json({
        "fecha": fecha,
        "picks": picks,
        "combinadas": combinadas
    }, output_path)

    log_envio("Fútbol", picks)


if __name__ == "__main__":
    generate_soccer_picks()
