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

# Constantes para consultas
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}
HOY = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")


def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    data = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params).json()
    games = []
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            home_pitcher = game["teams"]["home"].get("probablePitcher", {})
            away_pitcher = game["teams"]["away"].get("probablePitcher", {})
            games.append({
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "away_team_id": game["teams"]["away"]["team"]["id"]
            })
    return games

def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    data = requests.get(url, headers=HEADERS).json()
    splits = data.get("people", [{}])[0].get("stats", [{}])[0].get("splits", [])
    return splits[0].get("stat", {}) if splits else {}

def get_team_form(team_id):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    data = requests.get(url, headers=HEADERS).json()
    resultados = []
    for fecha in data.get("dates", []):
        for game in fecha.get("games", []):
            if game.get("status", {}).get("detailedState") != "Final": continue
            home = game["teams"]["home"]
            away = game["teams"]["away"]
            if home["team"]["id"] == team_id:
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

def get_team_avg(team_id):
    data = requests.get(MLB_TEAM_STATS_URL.format(team_id), headers=HEADERS).json()
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
    params = {"apiKey": ODDS_API_KEY, "regions": "us", "markets": "totals", "oddsFormat": "decimal"}
    return requests.get(ODDS_API_URL, headers=HEADERS, params=params).json()

def generar_mensaje_ia(partido, pick, cuota, linea, estimado):
    prompt = f"Genera un mensaje estilo canal premium de apuestas para Telegram.\nPartido: {partido}\nPick: {pick} @ {cuota} | Línea: {linea} | Estimado: {estimado} carreras.\nNo menciones IA ni OpenAI. Termina con '✅ Valor detectado en la cuota'."
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
        form_home = get_team_form(juego["home_team_id"])
        form_away = get_team_form(juego["away_team_id"])
        avg_home = get_team_avg(juego["home_team_id"])
        avg_away = get_team_avg(juego["away_team_id"])
        era_home = float(get_pitcher_stats(juego["home_pitcher_id"]).get("era", 99))
        era_away = float(get_pitcher_stats(juego["away_pitcher_id"]).get("era", 99))

        ajustado_home = ajustar_por_avg(ajustar_por_era(form_home["anotadas"], era_away), avg_home)
        ajustado_away = ajustar_por_avg(ajustar_por_era(form_away["anotadas"], era_home), avg_away)
        estimado = round((ajustado_home + ajustado_away + form_home["recibidas"] + form_away["recibidas"]) / 2, 2)

        for odd in odds:
            if home in odd.get("home_team", "") and away in odd.get("away_team", ""):
                for o in odd["bookmakers"][0]["markets"]:
                    if o["key"] == "totals":
                        for outcome in o["outcomes"]:
                            if outcome["name"].lower() == "over":
                                linea = outcome["point"]
                                cuota = outcome["price"]
                                diferencia = estimado - linea

                                tipo = "normal"
                                if abs(diferencia) >= 3:
                                    tipo = "candado"
                                elif abs(diferencia) >= 2:
                                    tipo = "normal"
                                else:
                                    continue

                                pick = "Over" if diferencia > 0 else "Under"
                                mensaje = generar_mensaje_ia(f"{away} vs {home}", f"{pick} {linea}", cuota, linea, estimado)
                                enviar_a_telegram(mensaje, tipo)
                                print(f"✅ Enviado: {pick} {linea} ({tipo}) | {away} vs {home}")
                                break

if __name__ == "__main__":
    main()
