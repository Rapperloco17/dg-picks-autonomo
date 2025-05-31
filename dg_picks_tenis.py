import requests
from datetime import datetime
import os
import pytz
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Configuración inicial
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "").strip()
BASE_URL = "https://api.sportradar.com/tennis/trial/v2/en"

# Umbrales configurables para los picks
CONFIG = {
    "break": {
        "min_return_pct": 35,  # % mínimo de puntos ganados al resto
        "max_opponent_first_serve_pct": 65,  # % máximo de primer servicio del oponente
        "min_breaks_converted": 1,  # Mínimo de breaks convertidos
        "min_breaks_faced": 1  # Mínimo de breaks enfrentados por el oponente
    },
    "no_break": {
        "max_return_pct": 28,  # % máximo de puntos ganados al resto
        "min_opponent_first_serve_pct": 68,  # % mínimo de primer servicio del oponente
        "min_breaks_converted": 0  # Mínimo de breaks convertidos (0 para no romper)
    }
}

def get_nested(data: Dict, *keys, default=None) -> any:
    """Accede a claves anidadas de un diccionario de forma segura."""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError):
            return default
    return data

def obtener_partidos_hoy(timezone: str = "America/Mexico_City") -> List[Dict]:
    """Obtiene los partidos programados para hoy desde la API de Sportradar."""
    if not SPORTRADAR_API_KEY:
        raise ValueError("❌ La clave API de Sportradar no está configurada.")
    
    fecha = datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/schedules/{fecha}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return get_nested(response.json(), "sport_events", default=[])
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener partidos: {e}")
        return []

def obtener_estadisticas(match_id: str) -> Optional[Dict]:
    """Obtiene las estadísticas de un partido específico desde la API."""
    url = f"{BASE_URL}/matches/{match_id}/summary.json?api_key={SPORTRADAR_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener estadísticas para {match_id}: {e}")
        return None

def analizar_partido(partido: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Analiza un partido y genera picks de 'rompe' y 'no rompe'."""
    match_id = get_nested(partido, "id", default="")
    torneo = get_nested(partido, "tournament", "name", default="Torneo desconocido")
    hora_utc = get_nested(partido, "scheduled", default="")[:16].replace("T", " ")
    competidores = get_nested(partido, "competitors", default=[])

    if len(competidores) != 2:
        print(f"⚠️ Partido {match_id} no tiene exactamente 2 competidores.")
        return None, None

    jugador1 = get_nested(competidores[0], "name", default="Jugador 1")
    jugador2 = get_nested(competidores[1], "name", default="Jugador 2")

    stats = obtener_estadisticas(match_id)
    if not stats or not get_nested(stats, "sport_event_status", "statistics"):
        print(f"⚠️ Sin estadísticas para {jugador1} vs {jugador2}")
        return None, None

    try:
        estadisticas = get_nested(stats, "sport_event_status", "statistics", "competitors", default=[])
        if len(estadisticas) != 2:
            print(f"⚠️ Estadísticas incompletas para {jugador1} vs {jugador2}")
            return None, None

        stats1 = get_nested(estadisticas[0], "statistics", default={})
        stats2 = get_nested(estadisticas[1], "statistics", default={})

        # Estadísticas clave
        p1_return = get_nested(stats1, "receiving_points_won_pct", default=0)
        p1_breaks = get_nested(stats1, "break_points_converted", default=0)
        p2_1st_serve = get_nested(stats2, "first_serve_pct", default=100)
        p2_breaks_faced = get_nested(stats2, "break_points_faced", default=0)

        p2_return = get_nested(stats2, "receiving_points_won_pct", default=0)
        p2_breaks = get_nested(stats2, "break_points_converted", default=0)
        p1_1st_serve = get_nested(stats1, "first_serve_pct", default=100)
        p1_breaks_faced = get_nested(stats1, "break_points_faced", default=0)

        # Logs de debug
        print(f"📊 {jugador1} (return {p1_return}%, breaks {p1_breaks}) vs {jugador2} (1st serve {p2_1st_serve}%)")
        print(f"📊 {jugador2} (return {p2_return}%, breaks {p2_breaks}) vs {jugador1} (1st serve {p1_1st_serve}%)")

        pick_rompe = None
        pick_no_rompe = None

        # Pick: Rompe el servicio
        if (p1_return >= CONFIG["break"]["min_return_pct"] and
            p2_1st_serve <= CONFIG["break"]["max_opponent_first_serve_pct"] and
            p1_breaks >= CONFIG["break"]["min_breaks_converted"] and
            p2_breaks_faced >= CONFIG["break"]["min_breaks_faced"]):
            pick_rompe = {
                "partido": f"{jugador1} vs {jugador2}",
                "torneo": torneo,
                "hora": hora_utc,
                "pick": f"{jugador1} rompe el servicio en el primer set",
                "justificacion": (f"{jugador1} gana {p1_return}% al resto y ha convertido {p1_breaks} breaks. "
                                 f"{jugador2} solo acierta {p2_1st_serve}% con el primer saque y ha enfrentado "
                                 f"{p2_breaks_faced} breaks.")
            }

        # Pick: No rompe el servicio
        if (p2_return <= CONFIG["no_break"]["max_return_pct"] and
            p1_1st_serve >= CONFIG["no_break"]["min_opponent_first_serve_pct"] and
            p2_breaks == CONFIG["no_break"]["min_breaks_converted"]):
            pick_no_rompe = {
                "partido": f"{jugador2} vs {jugador1}",
                "torneo": torneo,
                "hora": hora_utc,
                "pick": f"{jugador2} NO rompe el servicio en el primer set",
                "justificacion": (f"{jugador2} solo gana {p2_return}% al resto, no ha convertido breaks y enfrenta "
                                 f"a un rival con {p1_1st_serve}% de primer servicio.")
            }

        return pick_rompe, pick_no_rompe
    except Exception as e:
        print(f"⚠️ Error en análisis de {jugador1} vs {jugador2}: {e}")
        return None, None

def imprimir_picks_estilo_dg(picks: List[Dict], tipo: str) -> str:
    """Genera una representación en Markdown de los picks."""
    output = [f"\n📌 PICKS: {tipo.upper()} 🔽"]
    for p in picks:
        output.extend([
            f"🎾 {p['partido']} – {p['torneo']}",
            f"🕐 Hora: {p['hora']} UTC",
            f"📌 Pick: {p['pick']}",
            f"📊 {p['justificacion']}",
            "✅ Valor detectado en la cuota\n"
        ])
    return "\n".join(output)

def guardar_picks_markdown(picks_rompe: List[Dict], picks_no_rompe: List[Dict], filename: str = "picks_tenis.md"):
    """Guarda los picks en un archivo Markdown."""
    content = ["# Picks de Tenis - " + datetime.now().strftime("%Y-%m-%d")]
    
    if picks_rompe:
        content.append(imprimir_picks_estilo_dg(picks_rompe, "rompe"))
    else:
        content.append("\n❌ No se detectaron jugadores que probablemente rompan el servicio.")
    
    if picks_no_rompe:
        content.append(imprimir_picks_estilo_dg(picks_no_rompe, "NO rompe"))
    else:
        content.append("\n❌ No se detectaron jugadores que probablemente NO rompan el servicio.")
    
    try:
        Path(filename).write_text("\n".join(content), encoding="utf-8")
        print(f"✅ Picks guardados en {filename}")
    except Exception as e:
        print(f"❌ Error al guardar picks: {e}")

# ===================== EJECUCIÓN =====================
if __name__ == "__main__":
    print("🔍 Buscando partidos y estadísticas reales...")
    
    try:
        partidos = obtener_partidos_hoy(timezone="America/Mexico_City")
        picks_rompe = []
        picks_no_rompe = []

        if not partidos:
            print("⚠️ No se encontraron partidos o hubo un error.")
        else:
            for p in partidos:
                pick1, pick2 = analizar_partido(p)
                if pick1:
                    picks_rompe.append(pick1)
                if pick2:
                    picks_no_rompe.append(pick2)

            # Imprimir y guardar picks
            if picks_rompe:
                print(imprimir_picks_estilo_dg(picks_rompe, "rompe"))
            else:
                print("\n❌ No se detectaron jugadores que probablemente rompan el servicio.")
            
            if picks_no_rompe:
                print(imprimir_picks_estilo_dg(picks_no_rompe, "NO rompe"))
            else:
                print("\n❌ No se detectaron jugadores que probablemente NO rompan el servicio.")
            
            # Guardar en archivo Markdown
            guardar_picks_markdown(picks_rompe, picks_no_rompe)
    
    except Exception as e:
        print(f"❌ Error en la ejecución principal: {e}")
