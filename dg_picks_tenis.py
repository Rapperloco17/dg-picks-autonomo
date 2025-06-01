import requests
from datetime import datetime
import os
import pytz
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time

# Configuración inicial
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "").strip()
BASE_URL = "https://api.sportradar.com/tennis/trial/v2/en"

# Umbrales configurables para los picks
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

# Contador global de solicitudes
REQUEST_COUNT = 0
MAX_REQUESTS = 1000  # Límite de la API de prueba

def get_nested(data: Dict, *keys, default=None) -> any:
    """Accede a claves anidadas de un diccionario de forma segura."""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError):
            return default
    return data

def obtener_partidos_atp_challenger(timezone: str = "America/Mexico_City", max_partidos: int = 5) -> List[Dict]:
    """Obtiene los partidos programados para hoy de la ATP y Challenger desde la API de Sportradar."""
    global REQUEST_COUNT
    if not SPORTRADAR_API_KEY:
        raise ValueError("❌ La clave API de Sportradar no está configurada.")
    
    if REQUEST_COUNT >= MAX_REQUESTS:
        print(f"❌ Límite de {MAX_REQUESTS} solicitudes alcanzado.")
        return []
    
    fecha_actual = datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/schedules/{fecha_actual}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        REQUEST_COUNT += 1
        print(f"📈 Solicitudes realizadas: {REQUEST_COUNT}/{MAX_REQUESTS}")
        time.sleep(2)  # Pausa de 2 segundos
        partidos = get_nested(response.json(), "sport_events", default=[])
        
        # Filtrar partidos de ATP o Challenger, programados para hoy y en estados relevantes
        partidos_filtrados = []
        for p in partidos:
            torneo = get_nested(p, "tournament", "name", default="").upper()
            scheduled = get_nested(p, "scheduled", default="")
            status = get_nested(p, "sport_event_status", "status", default="")

            # Verificar que sea un torneo ATP o Challenger
            if torneo.find("ATP") == -1 and torneo.find("CHALLENGER") == -1:
                continue

            # Verificar que el partido sea del día actual
            if not scheduled.startswith(fecha_actual):
                continue

            # Verificar que el partido esté programado o en curso
            if status not in ["not_started", "inprogress"]:
                continue

            partidos_filtrados.append(p)

        print(f"🎾 Encontrados {len(partidos_filtrados)} partidos ATP/Challenger válidos.")
        return partidos_filtrados[:max_partidos]  # Limita a 5 partidos
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener partidos ATP/Challenger: {e}")
        return []

def obtener_estadisticas(match_id: str) -> Optional[Dict]:
    """Obtiene las estadísticas de un partido específico desde la API con reintentos."""
    global REQUEST_COUNT
    if REQUEST_COUNT >= MAX_REQUESTS:
        print(f"❌ Límite de {MAX_REQUESTS} solicitudes alcanzado.")
        return None
    
    url = f"{BASE_URL}/matches/{match_id}/summary.json?api_key={SPORTRADAR_API_KEY}"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            REQUEST_COUNT += 1
            print(f"📈 Solicitudes realizadas: {REQUEST_COUNT}/{MAX_REQUESTS}")
            time.sleep(2)  # Pausa de 2 segundos
            data = response.json()
            # Verificar que el partido tenga estadísticas y que el estado sea relevante
            status = get_nested(data, "sport_event_status", "status", default="")
            if status not in ["inprogress"]:
                print(f"⚠️ Partido {match_id} no está en curso (estado: {status}).")
                return None
            if not get_nested(data, "sport_event_status", "statistics"):
                print(f"⚠️ No hay estadísticas disponibles para el partido {match_id}.")
                return None
            return data
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"⚠️ Límite alcanzado (429). Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                print(f"❌ Error al obtener estadísticas para {match_id}: {e}")
                return None
    print(f"❌ Máximo de reintentos alcanzado para {match_id}")
    return None

def analizar_partido(partido: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Analiza un partido ATP/Challenger y genera picks de 'rompe' y 'no rompe'."""
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

        p1_return = get_nested(stats1, "receiving_points_won_pct", default=0)
        p1_breaks = get_nested(stats1, "break_points_converted", default=0)
        p2_1st_serve = get_nested(stats2, "first_serve_pct", default=100)
        p2_breaks_faced = get_nested(stats2, "break_points_faced", default=0)

        p2_return = get_nested(stats2, "receiving_points_won_pct", default=0)
        p2_breaks = get_nested(stats2, "break_points_converted", default=0)
        p1_1st_serve = get_nested(stats1, "first_serve_pct", default=100)
        p1_breaks_faced = get_nested(stats1, "break_points_faced", default=0)

        print(f"📊 {jugador1} (return {p1_return}%, breaks {p1_breaks}) vs {jugador2} (1st serve {p2_1st_serve}%)")
        print(f"📊 {jugador2} (return {p2_return}%, breaks {p2_breaks}) vs {jugador1} (1st serve {p1_1st_serve}%)")

        pick_rompe = None
        pick_no_rompe = None

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

def guardar_picks_markdown(picks_rompe: List[Dict], picks_no_rompe: List[Dict], filename: str = "picks_tenis_atp_challenger.md"):
    """Guarda los picks en un archivo Markdown."""
    content = ["# Picks de Tenis ATP/Challenger - " + datetime.now().strftime("%Y-%m-%d")]
    
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
    print("🔍 Buscando partidos ATP/Challenger y estadísticas reales...")
    
    try:
        partidos = obtener_partidos_atp_challenger(timezone="America/Mexico_City")
        picks_rompe = []
        picks_no_rompe = []

        if not partidos:
            print("⚠️ No se encontraron partidos ATP/Challenger válidos para hoy o hubo un error.")
        else:
            for p in partidos:
                pick1, pick2 = analizar_partido(p)
                if pick1:
                    picks_rompe.append(pick1)
                if pick2:
                    picks_no_rompe.append(pick2)

            if picks_rompe:
                print(imprimir_picks_estilo_dg(picks_rompe, "rompe"))
            else:
                print("\n❌ No se detectaron jugadores que probablemente rompan el servicio.")
            
            if picks_no_rompe:
                print(imprimir_picks_estilo_dg(picks_no_rompe, "NO rompe"))
            else:
                print("\n❌ No se detectaron jugadores que probablemente NO rompan el servicio.")
            
            guardar_picks_markdown(picks_rompe, picks_no_rompe)
    
    except Exception as e:
        print(f"❌ Error en la ejecución principal: {e}")
