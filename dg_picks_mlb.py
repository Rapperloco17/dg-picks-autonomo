
# dg_picks_mlb.py – Sistema completo: Over/Under + ML + RL + OpenAI + Telegram

import os
import requests
import openai
from datetime import datetime, timedelta
import pytz

# Configuración desde Railway
openai.api_key = os.getenv("OPENAI_API_KEY")
token_telegram = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id_vip = os.getenv("CHAT_ID_VIP")
chat_id_free = os.getenv("CHAT_ID_FREE")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Constantes de API
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}
HOY = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")

def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    data = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params).json()
    games = []
    for d in data.get("dates", []):
        for g in d.get("games", []):
            home_pitcher = g["teams"]["home"].get("probablePitcher", {})
            away_pitcher = g["teams"]["away"].get("probablePitcher", {})
            games.append({
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),
                "home_team_id": g["teams"]["home"]["team"]["id"],
                "away_team_id": g["teams"]["away"]["team"]["id"]
            })
    return games

def get_pitcher_stats(pitcher_id):
    if not pitcher_id: return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    data = requests.get(url, headers=HEADERS).json()
    stats = data.get("people", [{}])[0].get("stats", [{}])[0].get("splits", [])
    return stats[0].get("stat", {}) if stats else {}

def get_team_form(team_id):
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start, end)
    data = requests.get(url, headers=HEADERS).json()
    resultados = []
    for fecha in data.get("dates", []):
        for g in fecha.get("games", []):
            if g.get("status", {}).get("detailedState") != "Final": continue
            h, a = g["teams"]["home"], g["teams"]["away"]
            if h["team"]["id"] == team_id: anot, rec = h["score"], a["score"]
            else: anot, rec = a["score"], h["score"]
            resultados.append((anot, rec))
    ult = resultados[-5:]
    return {
        "anotadas": round(sum(x[0] for x in ult) / len(ult), 2),
        "recibidas": round(sum(x[1] for x in ult) / len(ult), 2)
    } if ult else {"anotadas": 0, "recibidas": 0}

def get_team_avg(team_id):
    stats = requests.get(MLB_TEAM_STATS_URL.format(team_id), headers=HEADERS).json()
    try: return float(stats["stats"][0]["splits"][0]["stat"]["battingAvg"])
    except: return 0.25

def ajustar_por_era(base, era):
    if era < 2.5: return base - 0.7
    if era < 3.5: return base - 0.3
    if era < 4.5: return base
    if era < 5.5: return base + 0.5
    return base + 0.8

def ajustar_por_avg(base, avg):
    if avg < 0.230: return base - 0.5
    if avg < 0.250: return base - 0.2
    if avg < 0.270: return base
    if avg < 0.290: return base + 0.3
    return base + 0.6

def get_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    return requests.get(ODDS_API_URL, headers=HEADERS, params=params).json()

def generar_mensaje_ia(partido, pick, cuota, linea, estimado):
    prompt = f"Genera un mensaje estilo canal premium para Telegram.
Partido: {partido}
Pick: {pick} @ {cuota} | Línea: {linea} | Estimado: {estimado} carreras.
Termina con '✅ Valor detectado en la cuota'."
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return res.choices[0].message.content.strip()

def enviar_a_telegram(mensaje, tipo):
    destino = chat_id_vip if tipo == "candado" else chat_id_free
    url = f"https://api.telegram.org/bot{token_telegram}/sendMessage"
    requests.post(url, data={"chat_id": destino, "text": mensaje, "parse_mode": "HTML"})

def main():
    print("🔍 Ejecutando DG Picks MLB completo")
    juegos = get_today_mlb_games()
    odds = get_odds()

    for juego in juegos:
        home = juego["home_team"]
        away = juego["away_team"]
        form_h = get_team_form(juego["home_team_id"])
        form_a = get_team_form(juego["away_team_id"])
        avg_h = get_team_avg(juego["home_team_id"])
        avg_a = get_team_avg(juego["away_team_id"])
        era_h = float(get_pitcher_stats(juego["home_pitcher_id"]).get("era", 99))
        era_a = float(get_pitcher_stats(juego["away_pitcher_id"]).get("era", 99))

        ajust_h = ajustar_por_avg(ajustar_por_era(form_h["anotadas"], era_a), avg_h)
        ajust_a = ajustar_por_avg(ajustar_por_era(form_a["anotadas"], era_h), avg_a)
        estimado = round((ajust_h + ajust_a + form_h["recibidas"] + form_a["recibidas"]) / 2, 2)

        for odd in odds:
            if home in odd.get("home_team", "") and away in odd.get("away_team", ""):
                mercados = odd["bookmakers"][0]["markets"]
                linea, cuota = None, None
                for m in mercados:
                    if m["key"] == "totals":
                        for o in m["outcomes"]:
                            if o["name"].lower() == "over":
                                linea = o["point"]
                                cuota = o["price"]
                if not linea or not cuota:
                    continue

                diferencia = estimado - linea
                tipo = "candado" if abs(diferencia) >= 3 else "normal" if abs(diferencia) >= 2 else None
                if not tipo:
                    continue

                pick = "Over" if diferencia > 0 else "Under"
                mensaje = generar_mensaje_ia(f"{away} vs {home}", f"{pick} {linea}", cuota, linea, estimado)
                enviar_a_telegram(mensaje, tipo)
                print(f"✅ Enviado: {pick} {linea} ({tipo}) | {away} vs {home}")

if __name__ == "__main__":
    main()
