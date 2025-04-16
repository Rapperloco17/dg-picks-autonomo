import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_URL = "https://www.sofascore.com"

# Obtener partidos del día (ATP y Challenger)
def obtener_partidos_reales():
    url = f"{BASE_URL}/tennis"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    partidos = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/tennis/" in href and "-vs-" in href and not any(t in href for t in ["doubles", "itf"]):
            slug = href.strip("/")
            jugadores = slug.split("/")[-1].split("-vs-")
            if len(jugadores) == 2:
                partidos.append({
                    "partido": slug,
                    "player_a": jugadores[0],
                    "player_b": jugadores[1]
                })
    return partidos[:6]  # Máximo 6 partidos para evitar sobrecarga

# Simular estadísticas de jugador
# (Esto se reemplazará más adelante por scraping real por jugador)
def get_stats_jugador(nombre):
    time.sleep(2)  # Delay para no ser detectado
    return {
        "rompimientos_1er_set": 4,
        "partidos_analizados": 5,
        "ratio": 0.72,
        "bp_creados": 3.5,
        "bp_concedidos": 2.1,
        "retorno": 43,
        "superficie": "arcilla"
    }

def guardar_analisis(resultados):
    fecha = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)
    with open(f"data/rompimientos_{fecha}.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

def obtener_picks_tenis():
    partidos = obtener_partidos_reales()
    if not partidos:
        return []

    stats_por_jugador = {}
    picks = []

    for match in partidos:
        a = match["player_a"]
        b = match["player_b"]

        if a not in stats_por_jugador:
            stats_por_jugador[a] = get_stats_jugador(a)
        if b not in stats_por_jugador:
            stats_por_jugador[b] = get_stats_jugador(b)

        stats_a = stats_por_jugador[a]
        stats_b = stats_por_jugador[b]

        partido = f"{a.title()} vs {b.title()}"

        for stats, nombre in [(stats_a, a), (stats_b, b)]:
            ratio = stats["ratio"]
            analisis = (
                f"{nombre.title()} ha roto en el 1er set en {int(ratio * 100)}% de sus 
                últimos {stats['partidos_analizados']} partidos en {stats['superficie']}. 
                Genera {stats['bp_creados']} BP, gana {stats['retorno']}% al resto.",
                concede {stats['bp_concedidos']} BP por set."
            )
            if ratio > 0.7:
                picks.append({
                    "partido": partido,
                    "pick": f"{nombre.title()} rompe en el primer set",
                    "analisis": analisis,
                    "cuota": "1.82",
                    "canal": "privado",
                    "stake": "2/10"
                })
            elif ratio < 0.3:
                picks.append({
                    "partido": partido,
                    "pick": f"{nombre.title()} NO rompe en el primer set",
                    "analisis": analisis,
                    "cuota": "1.95",
                    "canal": "privado",
                    "stake": "2/10"
                })

        if stats_a["ratio"] > 0.7 and stats_b["ratio"] > 0.7:
            picks.append({
                "partido": partido,
                "pick": "Ambos rompen en el primer set",
                "analisis": (
                    f"{a.title()} y {b.title()} tienen alta tasa de rompimiento: 
                    {int(stats_a['ratio']*100)}% y {int(stats_b['ratio']*100)}%. 
                    Ambos generan +2.5 BP por set y juegan en {stats_a['superficie']}."
                ),
                "cuota": "2.10",
                "canal": "privado",
                "stake": "1/10"
            })

    guardar_analisis(stats_por_jugador)
    return picks
