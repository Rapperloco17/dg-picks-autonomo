import requests
import json
from datetime import datetime
from utils.soccer_utils import analyze_match, get_soccer_matches
from utils.odds_api import get_odds_for_match
from utils.telegram import log_envio

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
                    "analisis": analysis['reason'],
                    "canal": "vip"
                }
                picks.append(pick_data)

    # Clasificación de combinadas
    total_cuota = 1
    conservadora_cuota = 1
    for pick in picks[:5]:
        total_cuota *= float(pick['cuota'])
    for pick in picks[:3]:
        conservadora_cuota *= float(pick['cuota'])

    if 50 <= total_cuota < 150:
        nombre = "Parlay Soñador"
        mensaje = message_templates['soñadora']
        combinadas.append({
            "nombre": nombre,
            "cuota_total": round(total_cuota, 2),
            "picks": picks[:5],
            "mensaje": mensaje
        })
        log_envio("vip", f"{mensaje}\n\nCuota total: {round(total_cuota, 2)}")
        log_envio("free", f"{mensaje}\n(Exclusiva completa solo en el canal VIP)")
    elif total_cuota >= 150:
        nombre = "Bomba Legendaria"
        mensaje = message_templates['bomba']
        combinadas.append({
            "nombre": nombre,
            "cuota_total": round(total_cuota, 2),
            "picks": picks[:5],
            "mensaje": mensaje
        })
        log_envio("vip", f"{mensaje}\n\nCuota total: {round(total_cuota, 2)}")
        log_envio("free", f"{mensaje}\n(Exclusiva completa solo en el canal VIP)")

    # Parlay conservador
    if 2.00 <= conservadora_cuota <= 3.50:
        nombre = "Parlay Conservador del Día"
        mensaje = (
            f"🛡️ *Parlay Conservador del Día*\n"
            f"🎯 Selección combinada con picks sólidos y alto respaldo estadístico.\n"
            f"💰 Cuota total: @{round(conservadora_cuota, 2)}\n"
            f"📊 Análisis real y valor validado en cada elección.\n\n"
            f"✅ Pensado para los que prefieren control y consistencia.\n"
            f"📍 Exclusivo del canal VIP.\n\n"
            f"*No es magia, es estadística.* 🧠"
        )
        combinadas.append({
            "nombre": nombre,
            "cuota_total": round(conservadora_cuota, 2),
            "picks": picks[:3],
            "mensaje": mensaje
        })
        log_envio("vip", mensaje)

    # Enviar picks
    for i, pick in enumerate(picks):
        pick_msg = (
            f"⚽ *Pick Fútbol*\n"
            f"📅 Partido: {pick['partido']}\n"
            f"🏆 Liga: {pick['liga']}\n"
            f"📊 Análisis: {pick['analisis']}\n"
            f"💰 Cuota: {pick['cuota']}\n"
            f"✅ Valor detectado en la cuota."
        )
        canal = "vip" if i >= 3 else "free"
        log_envio(canal, pick_msg)

    # Guardado
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = f"{OUTPUT_FOLDER}futbol_{fecha_hoy}.json"
    save_json({"picks": picks, "combinadas": combinadas}, archivo_salida)
    print(f"Guardado en: {archivo_salida}")

if __name__ == "__main__":
    generate_soccer_picks()
