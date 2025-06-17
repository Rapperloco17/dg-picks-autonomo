import requests
import openai
import os
import asyncio
import logging
import pytz
import json
import hashlib
from datetime import datetime
from telegram import Bot
from fuzzywuzzy import fuzz
from openai import OpenAI

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Zona horaria y fecha
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")

# Umbrales configurables para sugerir picks
PICK_THRESHOLDS = {
    "low_odds": {"max_odds": 1.70, "min_runs": 4.0, "max_era": 3.5, "label": "Valor medio"},
    "mid_odds": {"min_odds": 1.70, "max_odds": 2.30, "min_runs": 4.0, "max_era": 4.2, "label": "Valor sólido"},
    "high_odds": {"min_odds": 2.30, "min_runs": 4.5, "max_era": 4.5, "label": "Underdog con ataque"}
}

# URLs
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
HEADERS = {"User-Agent": "DG Picks"}

def check_env_vars():
    """Valida que todas las variables de entorno necesarias estén definidas."""
    required_vars = ["ODDS_API_KEY", "OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN"]
    # Verificar al menos una variable de chat ID
    chat_vars = ["CHAT_ID_VIP", "CHAT_ID_FREE", "chat_id_reto"]
    missing_chat = [var for var in chat_vars if not os.getenv(var)]
    if len(missing_chat) == len(chat_vars):
        logger.warning("Ninguna variable de chat ID encontrada, pero el script intentará continuar")
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

def is_mlb_season(date: datetime) -> bool:
    """Verifica si la fecha está dentro de la temporada de MLB (marzo a octubre)."""
    if not (3 <= date.month <= 10):
        logger.warning("No es temporada de MLB, ejecución detenida")
        return False
    return True

def normalize(name: str) -> str:
    """Normaliza nombres de equipos para comparación."""
    return name.lower().replace(" ", "").replace("-", "")

def find_matching_team(team_name: str, odds_data: list) -> dict:
    """Encuentra un partido en los datos de cuotas usando coincidencia aproximada."""
    team_name_norm = normalize(team_name)
    for odds in odds_data:
        home_norm = normalize(odds["home_team"])
        away_norm = normalize(odds["away_team"])
        if fuzz.ratio(team_name_norm, home_norm) > 85 or fuzz.ratio(team_name_norm, away_norm) > 85:
            return odds
    return None

def get_today_games() -> list:
    """
    Obtiene la lista de partidos de MLB programados para hoy.
    Returns:
        list: Lista de diccionarios con información de cada partido.
    Raises:
        requests.RequestException: Si la solicitud a la API falla.
    """
    try:
        params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
        res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        games = []
        for date_info in data.get("dates", []):
            for g in date_info.get("games", []):
                games.append({
                    "home": g["teams"]["home"]["team"]["name"],
                    "away": g["teams"]["away"]["team"]["name"],
                    "home_id": g["teams"]["home"]["team"]["id"],
                    "away_id": g["teams"]["away"]["team"]["id"],
                    "pitcher_home": g["teams"]["home"].get("probablePitcher", {}).get("id"),
                    "pitcher_away": g["teams"]["away"].get("probablePitcher", {}).get("id"),
                    "venue": g["venue"]["name"]
                })
        logger.info(f"Obtenidos {len(games)} partidos para {HOY}")
        return games
    except Exception as e:
        logger.error(f"Error al obtener partidos: {e}")
        return []

def get_full_season_form(team_id: int) -> dict:
    """
    Calcula el promedio de carreras anotadas y recibidas por un equipo en la temporada.
    Args:
        team_id: ID del equipo.
    Returns:
        dict: Estadísticas de carreras anotadas, recibidas y juegos jugados.
    """
    try:
        url = MLB_RESULTS_URL.format(team_id, HOY)
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        juegos = []
        for d in res.json().get("dates", []):
            for g in d.get("games", []):
                if g["status"]["detailedState"] != "Final":
                    continue
                home, away = g["teams"]["home"], g["teams"]["away"]
                if home["team"]["id"] == team_id:
                    anotadas, recibidas = home["score"], away["score"]
                else:
                    anotadas, recibidas = away["score"], home["score"]
                juegos.append((anotadas, recibidas))
        if not juegos:
            return {}
        return {
            "anotadas": round(sum(j[0] for j in juegos) / len(juegos), 2),
            "recibidas": round(sum(j[1] for j in juegos) / len(juegos), 2),
            "juegos": len(juegos)
        }
    except Exception as e:
        logger.error(f"Error al obtener forma del equipo {team_id}: {e}")
        return {}

def get_pitcher_stats(pitcher_id: int) -> dict:
    """
    Obtiene las estadísticas de un pitcher para la temporada actual.
    Args:
        pitcher_id: ID del pitcher.
    Returns:
        dict: Estadísticas del pitcher (e.g., ERA).
    """
    if not pitcher_id:
        logger.warning("No pitcher ID provided, usando valores por defecto")
        return {"era": 99.0}
    try:
        url = PITCHER_STATS_URL.format(pitcher_id)
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
        stats = data.get("people", [])[0].get("stats", [])[0].get("splits", [])
        return stats[0].get("stat", {"era": 99.0}) if stats else {"era": 99.0}
    except Exception as e:
        logger.error(f"Error al obtener stats del pitcher {pitcher_id}: {e}")
        return {"era": 99.0}

def get_odds() -> list:
    """
    Obtiene las cuotas de apuestas para los partidos de MLB.
    Returns:
        list: Lista de cuotas por partido.
    Raises:
        Exception: Si falta la API Key o la solicitud falla.
    """
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    if not ODDS_API_KEY:
        raise Exception("❌ Falta la API Key de Odds")
    try:
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        res = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        logger.info("Cuotas obtenidas correctamente")
        return res.json()
    except Exception as e:
        logger.error(f"Error al obtener cuotas: {e}")
        return []

def sugerir_pick(equipo: str, form: dict, pitcher: dict, cuota_ml: float) -> str:
    """
    Sugiere un pick de apuesta basado en cuotas, forma del equipo y stats del pitcher.
    Args:
        equipo: Nombre del equipo.
        form: Estadísticas de forma del equipo.
        pitcher: Estadísticas del pitcher.
        cuota_ml: Cuota de la apuesta moneyline.
    Returns:
        str: Mensaje del pick sugerido o None si no hay valor.
    """
    try:
        era = float(pitcher.get("era", 99))
        anotadas = form.get("anotadas", 0)
        if not form or anotadas == 0:
            logger.warning(f"No hay datos de forma para {equipo}, pick no sugerido")
            return None
        for threshold in PICK_THRESHOLDS.values():
            if (threshold.get("min_odds", 0) <= cuota_ml <= threshold.get("max_odds", float('inf')) and
                anotadas >= threshold["min_runs"] and era < threshold["max_era"]):
                return f"🎯 {equipo} ML @ {cuota_ml} | {threshold['label']}: {anotadas}/j, ERA {era}"
        return None
    except Exception as e:
        logger.error(f"Error al sugerir pick para {equipo}: {e}")
        return None

async def enviar_telegram_async(mensaje: str):
    """Envía un mensaje a Telegram de forma asíncrona."""
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        # Priorizar CHAT_ID_VIP (canal premium) y caer a otras opciones si no está
        chat_id = os.getenv("CHAT_ID_VIP") or os.getenv("CHAT_ID_FREE") or os.getenv("chat_id_reto")
        if not chat_id:
            raise ValueError("No chat ID available")
        await bot.send_message(chat_id=chat_id, text=mensaje)
        logger.info(f"Mensaje enviado a Telegram al chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error al enviar a Telegram: {e}")

def get_cached_openai_response(prompt: str) -> str:
    """
    Obtiene una respuesta de OpenAI, usando caché si está disponible.
    Args:
        prompt: Texto del prompt para OpenAI.
    Returns:
        str: Respuesta generada o el prompt original si falla.
    """
    cache_file = "openai_cache.json"
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)
        if prompt_hash in cache:
            logger.info("Usando respuesta de OpenAI desde caché")
            return cache[prompt_hash]
    except FileNotFoundError:
        cache = {}
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en apuestas deportivas y Telegram. Redacta el siguiente texto con estilo atractivo y profesional para un canal premium de MLB."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content
        cache[prompt_hash] = result
        with open(cache_file, "w") as f:
            json.dump(cache, f)
        logger.info("Respuesta de OpenAI almacenada en caché")
        return result
    except Exception as e:
        logger.error(f"Error con OpenAI: {e}")
        return prompt

async def main():
    """Función principal para generar y enviar pronósticos de MLB."""
    logger.info(f"📅 Iniciando pronósticos MLB – {HOY} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST")
    
    if not is_mlb_season(datetime.now(MX_TZ)):
        return

    try:
        juegos = get_today_games()
        cuotas = get_odds()
    except Exception as e:
        logger.error(f"Error al obtener datos iniciales: {e}")
        return

    resumen_picks = []
    for j in juegos:
        home, away = j["home"], j["away"]
        form_home = get_full_season_form(j["home_id"])
        form_away = get_full_season_form(j["away_id"])
        pitcher_home = get_pitcher_stats(j["pitcher_home"])
        pitcher_away = get_pitcher_stats(j["pitcher_away"])

        match = find_matching_team(home, cuotas)
        if not match:
            logger.warning(f"No se encontraron cuotas para {home} vs {away}")
            continue

        ml_teams = {o["name"]: o["price"] for b in match.get("bookmakers", []) for m in b.get("markets", []) if m["key"] == "h2h" for o in m.get("outcomes", [])}
        cuota_home = ml_teams.get(home)
        cuota_away = ml_teams.get(away)

        pick_home = sugerir_pick(home, form_home, pitcher_home, cuota_home) if cuota_home else None
        pick_away = sugerir_pick(away, form_away, pitcher_away, cuota_away) if cuota_away else None

        if pick_home:
            resumen_picks.append(f"⚔️ {away} @ {home}\n🧠 {pick_home}\n---")
        elif pick_away:
            resumen_picks.append(f"⚔️ {away} @ {home}\n🧠 {pick_away}\n---")

    if not resumen_picks:
        resumen_picks.append("⚠️ No se detectó valor en los partidos de hoy.")

    mensaje_base = f"📅 Pronósticos MLB – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n" + "\n".join(resumen_picks)

    mensaje_final = get_cached_openai_response(mensaje_base)

    await enviar_telegram_async(mensaje_final)

if __name__ == "__main__":
    check_env_vars()
    asyncio.run(main())
