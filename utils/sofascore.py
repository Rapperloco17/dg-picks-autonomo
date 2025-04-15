import requests
from bs4 import BeautifulSoup
import time
import random

HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B)"
    ])
}

BASE_URL = "https://www.sofascore.com"

# Simulador de jugador para ejemplo
EXAMPLE_PLAYERS = [
    "player/novak-djokovic/13415",
    "player/daniil-medvedev/68719",
    "player/carlos-alcaraz/102186"
]

def get_player_stats(player_slug):
    url = f"{BASE_URL}/{player_slug}"
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Simulador de análisis (aquí se personaliza en función del HTML real)
        rompimientos = random.randint(2, 5)
        total_partidos = 5

        time.sleep(random.uniform(1.5, 3.0))  # Delay anti-baneo

        return {
            "slug": player_slug,
            "rompimientos_1er_set": rompimientos,
            "partidos_analizados": total_partidos,
            "ratio": rompimientos / total_partidos
        }

    except Exception as e:
        print(f"❌ Error con {player_slug}: {e}")
        return None

def analizar_jugadores():
    resultados = []
    for jugador in EXAMPLE_PLAYERS:
        stats = get_player_stats(jugador)
        if stats:
            resultados.append(stats)
    return resultados

if __name__ == "__main__":
    analisis = analizar_jugadores()
    for dato in analisis:
        print(f"📊 {dato['slug']} - Rompe en 1er set: {dato['rompimientos_1er_set']} de {dato['partidos_analizados']} | Ratio: {dato['ratio']:.2f}")
