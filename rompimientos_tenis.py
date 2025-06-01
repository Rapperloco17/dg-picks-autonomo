import requests
import os
from datetime import datetime
import pytz
import time
from pathlib import Path
from typing import List, Dict, Optional

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "").strip()
BASE_URL = "https://api.sportradar.com/tennis/trial/v2/en"
MAX_REQUESTS = 1000
REQUEST_COUNT = 0

CONFIG = {
    "break": {
        "min_return_pct": 35,
        "max_opponent_first_serve_pct": 65,
        "min_breaks_converted": 1,
        "min_breaks_faced": 1
    },
    "no_break": {
        "max_return_pct": 28,
        "min_opponent_first_serve_pct": 68,
        "min_breaks_converted": 0
    }
}

jugadores_usados = []  # Para evitar duplicados en ML

def get_nested(data: Dict, *keys, default=None):
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError):
            return default
    return data

def obtener_partidos(timezone="America/Mexico_City", max_partidos=10) -> List[Dict]:
    global REQUEST_COUNT
    if not SPORTRADAR_API_KEY:
        raise ValueError("API key no configurada.")

    fecha_actual = datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/schedules/{fecha_actual}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        REQUEST_COUNT += 1
        time.sleep(2)
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

def obtener_estadisticas(match_id: str) -> Optional[Dict]:
    global REQUEST_COUNT
    if REQUEST_COUNT >= MAX_REQUESTS:
        return None

    url = f"{BASE_URL}/matches/{match_id}/summary.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        REQUEST_COUNT += 1
        time.sleep(2)
        return response.json()
    except:
        return None

def analizar_partido(p: Dict):
    match_id = get_nested(p, "id")
    comp = get_nested(p, "competitors", default=[])
    if len(comp) != 2:
        return None, None

    jugador1 = comp[0]["name"]
    jugador2 = comp[1]["name"]
    jugadores_usados.extend([jugador1, jugador2])

    stats = obtener_estadisticas(match_id)
    if not stats:
        return None, None

    estadisticas = get_nested(stats, "sport_event_status", "statistics", "competitors", default=[])
    if len(estadisticas) != 2:
        return None, None

    s1 = estadisticas[0]["statistics"]
    s2 = estadisticas[1]["statistics"]

    picks = {"rompe": None, "no_rompe": None}

    if (
        s1.get("receiving_points_won_pct", 0) >= CONFIG["break"]["min_return_pct"] and
        s2.get("first_serve_pct", 100) <= CONFIG["break"]["max_opponent_first_serve_pct"] and
        s1.get("break_points_converted", 0) >= CONFIG["break"]["min_breaks_converted"] and
        s2.get("break_points_faced", 0) >= CONFIG["break"]["min_breaks_faced"]
    ):
        picks["rompe"] = f"{jugador1} rompe el servicio en el primer set"

    if (
        s2.get("receiving_points_won_pct", 100) <= CONFIG["no_break"]["max_return_pct"] and
        s1.get("first_serve_pct", 0) >= CONFIG["no_break"]["min_opponent_first_serve_pct"] and
        s2.get("break_points_converted", 1) == CONFIG["no_break"]["min_breaks_converted"]
    ):
        picks["no_rompe"] = f"{jugador2} NO rompe el servicio en el primer set"

    return picks

def imprimir_picks(picks_totales: List[Dict]):
    print("# 🎾 Picks de rompimientos en 1er set\n")
    for p in picks_totales:
        for tipo, pick in p.items():
            if pick:
                print(f"📌 {pick}  ✅ Valor detectado en la cuota\n")

def guardar_md(picks_totales: List[Dict]):
    hoy = datetime.now().strftime("%Y-%m-%d")
    path = Path(f"picks_rompimiento_{hoy}.md")
    lines = ["# Picks de Rompimientos en Primer Set"]
    for p in picks_totales:
        for tipo, pick in p.items():
            if pick:
                lines.append(f"* {pick}  ✅")
    path.write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    partidos = obtener_partidos()
    picks = []
    for p in partidos:
        resultado = analizar_partido(p)
        if resultado:
            picks.append(resultado)

    imprimir_picks(picks)
    guardar_md(picks)
