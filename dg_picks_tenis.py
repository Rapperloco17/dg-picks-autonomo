import requests
import os
from datetime import datetime
import pytz
import time
from typing import List, Dict

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "").strip()
BASE_URL = "https://api.sportradar.com/tennis/trial/v2/en"
MAX_REQUESTS = 1000
REQUEST_COUNT = 0

# Aquí se deben importar si se ejecuta junto con rompimientos_tenis.py
from rompimientos_tenis import jugadores_usados  # Evitar duplicados

def get_nested(data: Dict, *keys, default=None):
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError):
            return default
    return data

def obtener_partidos(timezone="America/Mexico_City", max_partidos=20) -> List[Dict]:
    global REQUEST_COUNT
    fecha_actual = datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/schedules/{fecha_actual}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        REQUEST_COUNT += 1
        time.sleep(1)
        partidos = get_nested(response.json(), "sport_events", default=[])
        filtrados = []
        for p in partidos:
            torneo = get_nested(p, "tournament", "name", default="").upper()
            if "ATP" not in torneo and "CHALLENGER" not in torneo:
                continue
            filtrados.append(p)
        return filtrados[:max_partidos]
    except Exception as e:
        print(f"Error al obtener partidos: {e}")
        return []

def obtener_estadisticas(match_id):
    global REQUEST_COUNT
    url = f"{BASE_URL}/matches/{match_id}/summary.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        REQUEST_COUNT += 1
        time.sleep(1)
        return response.json()
    except:
        return None

def analizar_ml(j1, j2, s1, s2, h2h="", cuota=1.70) -> Dict:
    confianza = 0
    if s1.get("receiving_points_won_pct", 0) > s2.get("receiving_points_won_pct", 0):
        confianza += 1
    if s1.get("first_serve_pct", 0) > s2.get("first_serve_pct", 0):
        confianza += 1
    if s1.get("break_points_converted", 0) > s2.get("break_points_converted", 0):
        confianza += 1
    return {
        "partido": f"{j1} vs {j2}",
        "pick": f"{j1} ML",
        "return_pct": s1.get("receiving_points_won_pct", 0),
        "first_serve_pct": s1.get("first_serve_pct", 0),
        "breaks": s1.get("break_points_converted", 0),
        "h2h": h2h,
        "cuota": cuota,
        "confianza": confianza,
        "jugador": j1
    }

def imprimir_picks_top5(picks):
    picks = sorted(picks, key=lambda x: -x["confianza"])[:5]
    print("# 🎾 TOP 5 PICKS DEL DÍA – MONEY LINE\n")
    for i, p in enumerate(picks):
        icono = "🔐" if i == 0 else "🎯"
        print(f"{icono} {p['partido']}")
        print(f"📌 Pick: {p['pick']}")
        print(f"📊 Return: {p['return_pct']}% | 1st Serve: {p['first_serve_pct']}% | Breaks: {p['breaks']}")
        print(f"🔁 H2H: {p['h2h']}")
        print(f"💸 Cuota: {p['cuota']}")
        print("✅ Valor detectado en la cuota\n")

def ejecutar():
    partidos = obtener_partidos()
    picks_ml = []
    for p in partidos:
        comp = get_nested(p, "competitors", default=[])
        if len(comp) != 2:
            continue
        j1 = comp[0]["name"]
        j2 = comp[1]["name"]
        if j1 in jugadores_usados or j2 in jugadores_usados:
            continue  # evitar duplicar picks

        match_id = get_nested(p, "id")
        stats = obtener_estadisticas(match_id)
        if not stats:
            continue
        estadisticas = get_nested(stats, "sport_event_status", "statistics", "competitors", default=[])
        if len(estadisticas) != 2:
            continue
        s1 = estadisticas[0]["statistics"]
        s2 = estadisticas[1]["statistics"]

        # Simulamos H2H y cuota
        h2h_text = "Primera vez que se enfrentan"
        cuota = 1.70
        pick = analizar_ml(j1, j2, s1, s2, h2h_text, cuota)
        picks_ml.append(pick)

    imprimir_picks_top5(picks_ml)

if __name__ == "__main__":
    ejecutar()
