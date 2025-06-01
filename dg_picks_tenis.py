import requests
import gzip
from io import BytesIO
from datetime import datetime, timedelta
import os
import pytz
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time

# Configuración inicial
GOALSERVE_API_KEY = os.getenv("GOALSERVE_API_KEY", "").strip()
BASE_URL = "http://www.goalserve.com/getfeed"
REQUEST_COUNT = 0
MAX_REQUESTS = 1000  # Ajustar según límites de Goalserve
LAST_TS = None  # Para manejar el parámetro ts

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

def get_nested(data: Dict, *keys, default=None) -> any:
    """Accede a claves anidadas de un diccionario de forma segura."""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError):
            return default
    return data

def make_request(url: str, use_ts: bool = False) -> Optional[Dict]:
    """Realiza una solicitud a la API de Goalserve manejando GZIP y ts."""
    global REQUEST_COUNT, LAST_TS
    if not GOALSERVE_API_KEY:
        raise ValueError("❌ La clave API de Goalserve no está configurada.")
    
    if REQUEST_COUNT >= MAX_REQUESTS:
        print(f"❌ Límite de {MAX_REQUESTS} solicitudes alcanzado.")
        return None
    
    # Añadir parámetro json=1 y ts si aplica
    params = "?json=1"
    if use_ts and LAST_TS:
        params += f"&ts={LAST_TS}"
    full_url = f"{url}/{GOALSERVE_API_KEY}/tennis_scores/{url}{params}"
    
    try:
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        REQUEST_COUNT += 1
        
        # Manejar GZIP
        if response.headers.get('Content-Encoding') == 'gzip':
            buf = BytesIO(response.content)
            with gzip.GzipFile(fileobj=buf) as gz:
                data = json.loads(gz.read().decode('utf-8'))
        else:
            data = response.json()
        
        # Actualizar LAST_TS si está presente
        ts = get_nested(data, "scores", "@ts", default=None)
        if ts:
            LAST_TS = ts
        
        print(f"📈 Solicitudes realizadas: {REQUEST_COUNT}/{MAX_REQUESTS}")
        time.sleep(2)  # Pausa de 2 segundos para evitar límites
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la solicitud a {url}: {e}")
        return None

def obtener_partidos_atp_challenger(timezone: str = "America/Mexico_City", max_partidos: int = 5, days_ahead: int = 0) -> List[Dict]:
    """Obtiene los partidos programados para una fecha específica."""
    fecha = (datetime.now(pytz.timezone(timezone)) + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # Obtener torneos ATP y Challenger
    atp_url = f"{BASE_URL}/atp_tournaments"
    challenger_url = f"{BASE_URL}/challenger_shedule"
    partidos = []
    
    for url in [atp_url, challenger_url]:
        data = make_request(url, use_ts=True)
        if not data:
            continue
        
        # Extraer partidos
        tournaments = get_nested(data, "scores", "category", default=[])
        if not isinstance(tournaments, list):
            tournaments = [tournaments]
        
        for tournament in tournaments:
            tournament_name = get_nested(tournament, "@name", default="").upper()
            if "ATP" not in tournament_name and "CHALLENGER" not in tournament_name:
                continue
            
            matches = get_nested(tournament, "match", default=[])
            if not isinstance(matches, list):
                matches = [matches]
            
            for match in matches:
                match_date = get_nested(match, "@date", default="")
                status = get_nested(match, "@status", default="")
                
                # Convertir formato de fecha dd.MM.yyyy a YYYY-MM-DD
                try:
                    match_date_converted = datetime.strptime(match_date, "%d.%m.%Y").strftime("%Y-%m-%d")
                except ValueError:
                    continue
                
                if match_date_converted != fecha:
                    continue
                
                if status not in ["Not Started", "Set 1", "Set 2", "Set 3", "Set 4"]:
                    continue
                
                match["tournament"] = {"name": tournament_name}
                partidos.append(match)
    
    print(f"🎾 Encontrados {len(partidos)} partidos ATP/Challenger válidos para {fecha}.")
    return partidos[:max_partidos]

def obtener_estadisticas(match_id: str) -> Optional[Dict]:
    """Obtiene las estadísticas de un partido específico."""
    url = f"{BASE_URL}/home_gamestats"
    data = make_request(url, use_ts=True)
    
    if not data:
        return None
    
    # Buscar el partido en las estadísticas en vivo
    categories = get_nested(data, "scores", "category", default=[])
    if not isinstance(categories, list):
        categories = [categories]
    
    for category in categories:
        matches = get_nested(category, "match", default=[])
        if not isinstance(matches, list):
            matches = [matches]
        
        for match in matches:
            if get_nested(match, "@id", default="") == match_id:
                return match
    
    # Si no se encuentra en estadísticas en vivo, buscar en datos históricos
    url_hist = f"{BASE_URL}/d-1_gamestats"
    data_hist = make_request(url_hist, use_ts=True)
    
    if not data_hist:
        print(f"⚠️ No hay estadísticas disponibles para el partido {match_id}.")
        return None
    
    categories_hist = get_nested(data_hist, "scores", "category", default=[])
    if not isinstance(categories_hist, list):
        categories_hist = [categories_hist]
    
    for category in categories_hist:
        matches = get_nested(category, "match", default=[])
        if not isinstance(matches, list):
            matches = [matches]
        
        for match in matches:
            if get_nested(match, "@id", default="") == match_id:
                return match
    
    print(f"⚠️ No hay estadísticas disponibles para el partido {match_id}.")
    return None

def analizar_partido(partido: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Analiza un partido ATP/Challenger y genera picks de 'rompe' y 'no rompe'."""
    match_id = get_nested(partido, "@id", default="")
    torneo = get_nested(partido, "tournament", "name", default="Torneo desconocido")
    hora_utc = f"{get_nested(partido, '@date', default='')} {get_nested(partido, '@time', default='')} UTC"
    
    players = get_nested(partido, "player", default=[])
    if len(players) != 2:
        print(f"⚠️ Partido {match_id} no tiene exactamente 2 jugadores.")
        return None, None
    
    jugador1 = get_nested(players[0], "@name", default="Jugador 1")
    jugador2 = get_nested(players[1], "@name", default="Jugador 2")
    
    stats = obtener_estadisticas(match_id)
    if not stats:
        print(f"⚠️ Sin estadísticas para {jugador1} vs {jugador2}")
        return None, None
    
    try:
        stats_players = get_nested(stats, "player", default=[])
        if len(stats_players) != 2:
            print(f"⚠️ Estadísticas incompletas para {jugador1} vs {jugador2}")
            return None, None
        
        stats1 = get_nested(stats_players[0], "stats", default={})
        stats2 = get_nested(stats_players[1], "stats", default={})
        
        # Extraer métricas relevantes
        p1_return = float(get_nested(stats1, "return_points_won", "@value", default=0))
        p1_breaks = int(get_nested(stats1, "break_points_converted", "@value", default=0))
        p2_1st_serve = float(get_nested(stats2, "first_serve", "@value", default=100))
        p2_breaks_faced = int(get_nested(stats2, "break_points_faced", "@value", default=0))
        
        p2_return = float(get_nested(stats2, "return_points_won", "@value", default=0))
        p2_breaks = int(get_nested(stats2, "break_points_converted", "@value", default=0))
        p1_1st_serve = float(get_nested(stats1, "first_serve", "@value", default=100))
        p1_breaks_faced = int(get_nested(stats1, "break_points_faced", "@value", default=0))
        
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
            f"🕐 Hora: {p['hora']}",
            f"📌 Pick: {p['pick']}",
            f"📊 {p['justificacion']}",
            "✅ Valor detectado en la cuota\n"
        ])
    return "\n".join(output)

def guardar_picks_markdown(picks_rompe: List[Dict], picks_no_rompe: List[Dict], filename: str = "picks_tenis_goalserve.md"):
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
