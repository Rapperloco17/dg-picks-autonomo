import requests
from bs4 import BeautifulSoup
import re
import random
import time

# Esta función es la principal para obtener picks de tenis desde Sofascore
def obtener_picks_tenis():
    url = "https://www.sofascore.com/es/tenis"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    partidos = soup.find_all("a", href=re.compile("tenis/"))
    urls_jugadores = []
    
    for link in partidos:
        href = link.get("href")
        if href and href.startswith("/jugador") and href.count("-") > 1:
            nombre_url = href.strip("/").split("/")[-1]
            if nombre_url not in urls_jugadores:
                urls_jugadores.append(nombre_url)

    urls_jugadores = list(set(urls_jugadores))[:6]  # Limitar a 6 jugadores para scraping controlado
    picks = []

    for jugador in urls_jugadores:
        stats = obtener_estadisticas_jugador(jugador)
        if not stats:
            continue

        nombre = stats["nombre"]
        ratio = stats["ratio_rompimientos"]
        superficie = stats["superficie"]

        analisis = []

        if ratio >= 0.6:
            analisis.append(
                f"{nombre.title()} ha roto en el 1er set en {int(ratio * 100)}% de sus partidos recientes."
            )
        elif 0.4 <= ratio < 0.6:
            analisis.append(
                f"{nombre.title()} tiene un ratio medio de rompimientos en el primer set: {int(ratio * 100)}%."
            )
        else:
            analisis.append(
                f"{nombre.title()} rara vez rompe en el primer set ({int(ratio * 100)}%)."
            )

        analisis.append(f"⭐ Datos basados en sus últimos partidos sobre {superficie}.")

        cuota = round(random.uniform(1.70, 2.20), 2)
        stake = random.choice(["1/10", "2/10", "3/10"])

        canal = random.choice(["vip", "free", "reto"])

        picks.append({
            "partido": f"{nombre} vs Rival",  # Esto se reemplazará cuando conectemos nombre real
            "pick": f"{nombre} rompe servicio en el 1er set",
            "cuota": cuota,
            "stake": stake,
            "canal": canal,
            "analisis": " ".join(analisis),
        })

        time.sleep(3)  # Delay para evitar detección de scraping

    return picks

# Esta es una función simulada que devuelve estadísticas de ejemplo para un jugador
def obtener_estadisticas_jugador(nombre_url):
    # Aquí se simulará temporalmente la obtención de estadísticas
    return {
        "nombre": nombre_url.replace("-", " ").title(),
        "ratio_rompimientos": round(random.uniform(0.3, 0.8), 2),
        "superficie": random.choice(["arcilla", "dura", "hierba"]),
    }
