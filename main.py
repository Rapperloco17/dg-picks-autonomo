# dg_picks_mlb.py – Ajuste total con picks ML, RL, Over/Under, conservador y Telegram

import os
import requests
import openai
from datetime import datetime, timedelta
import pytz

openai.api_key = os.getenv("OPENAI_API_KEY")
token_telegram = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id_vip = os.getenv("CHAT_ID_VIP")
chat_id_free = os.getenv("CHAT_ID_FREE")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}
MX_TZ = pytz.timezone("America/Mexico_City")
ESP_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

conservador_picks = []

def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    data = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params).json()
    games = []
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            hora_utc = datetime.strptime(game["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
            hora_mex = hora_utc.replace(tzinfo=pytz.utc).astimezone(MX_TZ).strftime("%H:%M")
            hora_esp = hora_utc.replace(tzinfo=pytz.utc).astimezone(ESP_TZ).strftime("%H:%M")
            home_pitcher = game["teams"]["home"].get("probablePitcher", {})
            away_pitcher = game["teams"]["away"].get("probablePitcher", {})
            games.append({
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),
                "home_pitcher_name": home_pitcher.get("fullName", "Por confirmar"),
                "away_pitcher_name": away_pitcher.get("fullName", "Por confirmar"),
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "away_team_id": game["teams"]["away"]["team"]["id"],
                "hora_mex": hora_mex,
                "hora_esp": hora_esp
            })
    return games

def get_pitcher_stats(pid):
    if not pid: return {}
    data = requests.get(MLB_PLAYER_STATS_URL.format(pid), headers=HEADERS).json()
    splits = data.get("people", [{}])[0].get("stats", [{}])[0].get("splits", [])
    return splits[0].get("stat", {}) if splits else {}

def get_team_form(tid):
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    data = requests.get(MLB_RESULTS_URL.format(tid, start, end), headers=HEADERS).json()
    resultados = []
    for fecha in data.get("dates", []):
        for game in fecha.get("games", []):
            if game.get("status", {}).get("detailedState") != "Final": continue
            home = game["teams"]["home"]
            away = game["teams"]["away"]
            if home["team"]["id"] == tid:
                anotadas, recibidas = home["score"], away["score"]
            else:
                anotadas, recibidas = away["score"], home["score"]
            resultados.append((anotadas, recibidas))
    if not resultados: return {"anotadas": 0, "recibidas": 0}
    ultimos = resultados[-5:]
    return {
        "anotadas": round(sum(x[0] for x in ultimos) / len(ultimos), 2),
        "recibidas": round(sum(x[1] for x in ultimos) / len(ultimos), 2)
    }

def get_team_avg(tid):
    data = requests.get(MLB_TEAM_STATS_URL.format(tid), headers=HEADERS).json()
    try:
        return float(data["stats"][0]["splits"][0]["stat"]["battingAvg"])
    except:
        return 0.25

def ajustar_por_era(base, era):
    if era < 2.5: return base - 0.7
    elif era < 3.5: return base - 0.3
    elif era < 4.5: return base
    elif era < 5.5: return base + 0.5
    else: return base + 0.8

def ajustar_por_avg(base, avg):
    if avg < 0.230: return base - 0.5
    elif avg < 0.250: return base - 0.2
    elif avg < 0.270: return base
    elif avg < 0.290: return base + 0.3
    else: return base + 0.6

def get_odds():
    params = {"apiKey": ODDS_API_KEY, "regions": "us", "markets": "h2h,spreads,totals", "oddsFormat": "decimal"}
    return requests.get(ODDS_API_URL, headers=HEADERS, params=params).json()

def generar_mensaje(match, tipo, pick, cuota, linea, estimado, hora_mex, hora_esp):
    bandera = "🇲🇽"; bandera_esp = "🇪🇸"
    encabezado = "🔐🔥 <b>CANDADO</b>" if tipo == "candado" else "✅ <b>Pick sugerido</b>"
    return f"{encabezado}\n\n<b>{match}</b>\n{bandera} {hora_mex}  |  {bandera_esp} {hora_esp}\n\n<b>{pick}</b> @ {cuota} | Línea: {linea}\nEstimado DG Picks: {estimado} carreras\n\n✅ Valor detectado en la cuota."

def enviar_a_telegram(msg, tipo):
    destino = chat_id_vip if tipo == "candado" else chat_id_free
    url = f"https://api.telegram.org/bot{token_telegram}/sendMessage"
    requests.post(url, data={"chat_id": destino, "text": msg, "parse_mode": "HTML"})

def main():
    juegos = get_today_mlb_games()
    odds = get_odds()

    for j in juegos:
        home, away = j["home_team"], j["away_team"]
        form_h = get_team_form(j["home_team_id"])
        form_a = get_team_form(j["away_team_id"])
        avg_h = get_team_avg(j["home_team_id"])
        avg_a = get_team_avg(j["away_team_id"])
        era_h = float(get_pitcher_stats(j["home_pitcher_id"]).get("era", 99))
        era_a = float(get_pitcher_stats(j["away_pitcher_id"]).get("era", 99))
        aj_h = ajustar_por_avg(ajustar_por_era(form_h["anotadas"], era_a), avg_h)
        aj_a = ajustar_por_avg(ajustar_por_era(form_a["anotadas"], era_h), avg_a)
        estimado = round((aj_h + aj_a + form_h["recibidas"] + form_a["recibidas"]) / 2, 2)

        for odd in odds:
            if home in odd.get("home_team", "") and away in odd.get("away_team", ""):
                cuotas = {o["key"]: o["outcomes"] for o in odd["bookmakers"][0]["markets"]}
                for outcome in cuotas.get("totals", []):
                    if outcome["name"].lower() == "over":
                        linea = outcome["point"]
                        cuota = outcome["price"]
                        diferencia = estimado - linea
                        tipo = "candado" if abs(diferencia) >= 3 else "normal" if abs(diferencia) >= 2 else None
                        if tipo:
                            pick = f"{'Over' if diferencia > 0 else 'Under'} {linea}"
                            mensaje = generar_mensaje(f"{away} vs {home}", tipo, pick, cuota, linea, estimado, j["hora_mex"], j["hora_esp"])
                            enviar_a_telegram(mensaje, tipo)
                            if tipo == "normal" and cuota <= 2.00:
                                conservador_picks.append((f"{pick} @ {cuota}", mensaje))
                            print(f"✅ {pick} {away} vs {home} [{tipo}]")

    # Parlay conservador
    if len(conservador_picks) >= 2:
        texto = "💵 <b>Parlay Conservador</b> – Cuota baja pero sólida\n\n"
        cuota_total = 1
        for pick, just in conservador_picks[:3]:
            texto += f"{pick}\n"
            cuota_total *= float(pick.split("@")[1].strip())
        texto += f"\n<b>Cuota total:</b> {round(cuota_total, 2)}\n\n✅ Ideal para armar stake bajo"
        enviar_a_telegram(texto, "free")

if __name__ == "__main__":
    main()
