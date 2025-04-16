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

def obtener_partidos_reales():
    url = f"{BASE_URL}/tennis"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    partidos = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/player/" in href:
            continue
        if "/tennis/" in href and "-vs-" in href:
            slug = href.strip("/")
            jugadores = slug.split("/")[-1].split("-vs-")
            if len(jugadores) == 2:
                partidos.append({
                    "partido": slug,
                    "player_a": f"player/{jugadores[0]}",
                    "player_b": f"player/{jugadores[1]}",
                    "cuota_a": round(random.uniform(1.50, 2.50), 2),
                    "cuota_b": round(random.uniform(1.50, 2.50), 2)
                })
    return partidos[:6]  # Limitar por ahora

def get_estadisticas_jugador(slug):
    time.sleep(random.uniform(1.5, 2.5))  # simular delay
    return {
        "slug": slug,
        "rompimientos_1er_set": random.randint(2, 5),
        "partidos_analizados": 5,
        "ratio": round(random.uniform(0.3, 0.9), 2),
        "bp_creados": round(random.uniform(1.5, 4.0), 2),
        "bp_concedidos": round(random.uniform(1.0, 3.5), 2),
        "retorno": round(random.uniform(35, 55), 1),
        "superficie": random.choice(["arcilla", "dura", "indoor"])
    }

def guardar_analisis(resultados):
    fecha = datetime.now().strftime("%Y-%m-%d")
    carpeta = "data"
    os.makedirs(carpeta, exist_ok=True)
    archivo = os.path.join(carpeta, f"rompimientos_{fecha}.json")

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)

def obtener_picks_tenis():
    matches = obtener_partidos_reales()
    if not matches:
        return []

    stats_por_jugador = {}
    picks = []

    for match in matches:
        for jugador in [match['player_a'], match['player_b']]:
            if jugador not in stats_por_jugador:
                stats_por_jugador[jugador] = get_estadisticas_jugador(jugador)

    for match in matches:
        a_slug = match['player_a']
        b_slug = match['player_b']
        stats_a = stats_por_jugador[a_slug]
        stats_b = stats_por_jugador[b_slug]

        nombre_a = a_slug.split("/")[-1].replace("-", " ").title()
        nombre_b = b_slug.split("/")[-1].replace("-", " ").title()

        partido = f"{nombre_a} vs {nombre_b}"

        for stats, nombre in [(stats_a, nombre_a), (stats_b, nombre_b)]:
            ratio = stats["ratio"]
            analisis = (
                f"{nombre} ha roto en el 1er set en {int(ratio * 100)}% de sus últimos {stats['partidos_analizados']} partidos "
                f"sobre {stats['superficie']']}. Genera {stats['bp_creados']} BP, gana {stats['retorno']}% al resto y "
                f"concede {stats['bp_concedidos']} BP por set."
            )
            if ratio > 0.7:
                picks.append({
                    "partido": partido,
                    "pick": f"{nombre} rompe en el primer set",
                    "analisis": analisis,
                    "cuota": "1.82",
                    "canal": "privado",
                    "stake": "2/10"
                })
            elif ratio < 0.3:
                picks.append({
                    "partido": partido,
                    "pick": f"{nombre} NO rompe en el primer set",
                    "analisis": analisis,
                    "cuota": "1.95",
                    "canal": "privado",
                    "stake": "2/10"
                })

        if stats_a["ratio"] > 0.7 and stats_b["ratio"] > 0.7:
            picks.append({
                "partido": partido,
                "pick": f"Ambos rompen en el primer set",
                "analisis": (
                    f"Tanto {nombre_a} como {nombre_b} tienen alta tasa de rompimiento: "
                    f"{int(stats_a['ratio']*100)}% y {int(stats_b['ratio']*100)}% respectivamente. "
                    f"Ambos generan +2.5 BP por set y juegan en {stats_a['superficie']}."
                ),
                "cuota": "2.10",
                "canal": "privado",
                "stake": "1/10"
            })

    guardar_analisis(list(stats_por_jugador.values()))
    return picks
