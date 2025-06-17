import requests
import os
import asyncio
import logging
import pytz
from datetime import datetime
from telegram import Bot

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Zona horaria y fecha
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
HEADERS = {"User-Agent": "DG Picks"}

def is_mlb_season(date: datetime) -> bool:
    """Verifica si la fecha está dentro de la temporada de MLB (marzo a octubre)."""
    if not (3 <= date.month <= 10):
        logger.warning("No es temporada de MLB, ejecución detenida")
        return False
    return True

async def enviar_telegram_async(mensaje):
    """Envía un mensaje a Telegram de forma asíncrona."""
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        chat_id = os.getenv("CHAT_ID_VIP") or os.getenv("CHAT_ID_FREE") or os.getenv("chat_id_reto")
        if not chat_id:
            raise ValueError("No chat ID available")
        await bot.send_message(chat_id=chat_id, text=mensaje)
        logger.info(f"Mensaje enviado a Telegram al chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error al enviar a Telegram: {e}")

def normalize(name):
    return name.lower().replace(" ", "").replace("-", "")

def get_today_games():
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
                "venue": g["venue"]["name"],
                "hora": datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ").astimezone(MX_TZ).strftime("%H:%M CST")
            })
    logger.info(f"Obtenidos {len(games)} partidos para {HOY}")
    return games

def get_full_season_form(team_id):
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

def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        logger.warning("No pitcher ID provided, usando valores por defecto")
        return {"era": 99.0, "nombre": "Desconocido"}
    url = PITCHER_STATS_URL.format(pitcher_id)
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    data = res.json()
    persona = data.get("people", [])[0]
    nombre = persona.get("fullName", "Desconocido")
    stats = persona.get("stats", [])[0].get("splits", [])
    era = stats[0].get("stat", {}).get("era", 99.0) if stats else 99.0
    return {"era": float(era), "nombre": nombre}

def get_odds():
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    if not ODDS_API_KEY:
        raise Exception("❌ Falta la API Key de Odds")
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

def score_valor(anotadas, era, cuota):
    if cuota == 0:
        return 0
    return round((anotadas * 10 / era) / cuota, 2)

def sugerir_picks():
    juegos = get_today_games()
    cuotas = get_odds()
    picks = []

    for j in juegos:
        home, away = j["home"], j["away"]
        form_home = get_full_season_form(j["home_id"])
        form_away = get_full_season_form(j["away_id"])
        pitcher_home = get_pitcher_stats(j["pitcher_home"])
        pitcher_away = get_pitcher_stats(j["pitcher_away"])

        match = next((o for o in cuotas if normalize(o["home_team"]) in normalize(home) and normalize(o["away_team"]) in normalize(away)), None)
        if not match:
            logger.warning(f"No se encontraron cuotas para {home} vs {away}")
            continue

        ml = {o["name"]: o["price"] for b in match["bookmakers"] for m in b["markets"] if m["key"] == "h2h" for o in m["outcomes"]}
        cuota_home = ml.get(home)
        cuota_away = ml.get(away)

        if cuota_home and form_home and pitcher_home:
            valor = score_valor(form_home["anotadas"], pitcher_home["era"], cuota_home)
            picks.append({
                "equipo": home, "cuota": cuota_home, "valor": valor,
                "anotadas": form_home["anotadas"], "pitcher": pitcher_home["nombre"],
                "era": pitcher_home["era"], "vs": away,
                "hora": j["hora"], "estadio": j["venue"]
            })
        if cuota_away and form_away and pitcher_away:
            valor = score_valor(form_away["anotadas"], pitcher_away["era"], cuota_away)
            picks.append({
                "equipo": away, "cuota": cuota_away, "valor": valor,
                "anotadas": form_away["anotadas"], "pitcher": pitcher_away["nombre"],
                "era": pitcher_away["era"], "vs": home,
                "hora": j["hora"], "estadio": j["venue"]
            })

    picks.sort(key=lambda x: x["valor"], reverse=True)
    return picks[:2]  # top 2

def armar_mensaje(picks):
    mensaje = f"📅 Pronósticos MLB – {FECHA_TEXTO}\n\n"
    for p in picks:
        mensaje += f"⚾ **{p['equipo']} vs {p['vs']}**\n"
        mensaje += f"🕒 {p['hora']} | {p['estadio']}\n"
        mensaje += f"👤 Pitcher: {p['pitcher']} (ERA {p['era']})\n"
        mensaje += f"🎯 Pick: {p['equipo']} ML @ {p['cuota']}\n"
        mensaje += f"🧠 Promedio de {p['anotadas']} carreras/juego. Valor detectado en cuota.\n---\n"
    if len(picks) == 2:
        cuota_total = round(picks[0]["cuota"] * picks[1]["cuota"], 2)
        mensaje += f"\n💥 Parlay sugerido: {picks[0]['equipo']} + {picks[1]['equipo']} ML @ {cuota_total}\n"
    return mensaje

async def main():
    if not is_mlb_season(datetime.now(MX_TZ)):
        await enviar_telegram_async(f"📅 Pronósticos MLB – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n⚠️ No es temporada de MLB.")
        return
    top_picks = sugerir_picks()
    if not top_picks:
        await enviar_telegram_async(f"📅 Pronósticos MLB – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n⚠️ No se detectaron picks con valor para hoy.")
        return
    mensaje = armar_mensaje(top_picks)
    await enviar_telegram_async(mensaje)

if __name__ == "__main__":
    asyncio.run(main())
