import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime
import os

HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B)"
    ])
}

BASE_URL = "https://www.sofascore.com"

EXAMPLE_MATCHES = [
    {
        "partido": "novak-djokovic-vs-carlos-alcaraz",
        "player_a": "player/novak-djokovic/13415",
        "player_b": "player/carlos-alcaraz/102186",
        "cuota_a": 1.75,
        "cuota_b": 2.10
    },
    {
        "partido": "daniil-medvedev-vs-stefanos-tsitsipas",
        "player_a": "player/daniil-medvedev/68719",
        "player_b": "player/stefanos-tsitsipas/56923",
        "cuota_a": 1.65,
        "cuota_b": 2.25
    }
]

def get_form_score(player_slug):
    try:
        time.sleep(random.uniform(1.5, 2.5))
        return random.randint(3, 5)  # simulador de forma
    except:
        return 0

def analizar_ml():
    picks_ml = []
    for match in EXAMPLE_MATCHES:
        form_a = get_form_score(match['player_a'])
        form_b = get_form_score(match['player_b'])

        favorito = "A" if form_a > form_b else "B"
        jugador = match['player_a'].split("/")[-1].replace("-", " ").title() if favorito == "A" else match['player_b'].split("/")[-1].replace("-", " ").title()
        cuota = match['cuota_a'] if favorito == "A" else match['cuota_b']

        picks_ml.append({
            "partido": match['partido'].replace("-", " ").title(),
            "pick": f"{jugador} gana el partido",
            "analisis": f"{jugador} llega con mejor forma reciente y mejores resultados en los últimos encuentros.",
            "cuota": str(cuota),
            "canal": "vip",
            "stake": "3/10"
        })
    return picks_ml

def guardar_analisis(resultados):
    fecha = datetime.now().strftime("%Y-%m-%d")
    carpeta = "data"
    os.makedirs(carpeta, exist_ok=True)
    archivo = os.path.join(carpeta, f"rompimientos_{fecha}.json")

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
    print(f"✅ Análisis guardado en {archivo}")

def analizar_jugadores():
    resultados = []
    for jugador in [m['player_a'] for m in EXAMPLE_MATCHES] + [m['player_b'] for m in EXAMPLE_MATCHES]:
        stats = {
            "slug": jugador,
            "rompimientos_1er_set": random.randint(2, 5),
            "partidos_analizados": 5,
            "ratio": round(random.uniform(0.4, 0.9), 2)
        }
        resultados.append(stats)
        time.sleep(random.uniform(1.5, 2.5))
    return resultados

def analizar_rompimientos_1set():
    picks_romp = []
    jugadores = analizar_jugadores()

    for j in jugadores:
        ratio = j['ratio']
        jugador = j['slug'].split("/")[-1].replace("-", " ").title()
        if ratio > 0.7:
            picks_romp.append({
                "partido": "Partido Desconocido",
                "pick": f"{jugador} rompe en el primer set",
                "analisis": f"{jugador} ha roto el servicio en el 1er set en {int(ratio * 10)}/10 de sus últimos partidos.",
                "cuota": "1.82",
                "canal": "vip"
            })
        elif ratio < 0.3:
            picks_romp.append({
                "partido": "Partido Desconocido",
                "pick": f"{jugador} NO rompe en el primer set",
                "analisis": f"{jugador} rara vez rompe el servicio temprano: ratio de {ratio:.2f} en los últimos partidos.",
                "cuota": "1.95",
                "canal": "free"
            })

    return picks_romp

if __name__ == "__main__":
    analisis = analizar_jugadores()
    guardar_analisis(analisis)
    ml_picks = analizar_ml()
    for pick in ml_picks:
        print(f"📊 ML PICK: {pick['partido']} | {pick['pick']} @ {pick['cuota']} | {pick['analisis']}")

