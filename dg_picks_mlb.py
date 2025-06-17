import os
import requests
from datetime import datetime, timedelta
import pytz

# Zona horaria
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

# ✅ API Key desde variable de entorno
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# URLs
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_API_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"

HEADERS = {"User-Agent": "DG Picks"}

# Obtener partidos de hoy
def get_today_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
    res = requests.get(MLB_API_URL, headers=HEADERS, params=params, timeout=10)
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
    return games

# Forma del equipo (últimos 10 juegos)
def get_team_form(team_id):
    end_date = HOY
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    resultados = []
    for d in res.json().get("dates", []):
        for g in d.get("games", []):
            if g["status"]["detailedState"] != "Final":
                continue
            home, away = g["teams"]["home"], g["teams"]["away"]
            if home["team"]["id"] == team_id:
                anotadas, recibidas = home["score"], away["score"]
                victoria = anotadas > recibidas
            else:
                anotadas, recibidas = away["score"], home["score"]
                victoria = anotadas > recibidas
            resultados.append((anotadas, recibidas, victoria))
    ultimos = resultados[-10:]
    if not ultimos:
        return {}
    return {
        "anotadas": round(sum(x[0] for x in ultimos) / len(ultimos), 2),
        "recibidas": round(sum(x[1] for x in ultimos) / len(ultimos), 2),
        "victorias": sum(1 for x in ultimos if x[2])
    }

# Stats pitcher
def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = PITCHER_STATS_URL.format(pitcher_id)
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    data = res.json()
    stats = data.get("people", [])[0].get("stats", [])[0].get("splits", [])
    return stats[0].get("stat", {}) if stats else {}

# Cuotas
def get_odds():
    if not ODDS_API_KEY:
        raise Exception("❌ No se encontró la variable ODDS_API_KEY")
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    res = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
    res.raise_for_status()
    return res.json()

# Normalizar nombres
def normalize(name):
    return name.lower().replace(" ", "").replace("-", "")

# Sugerir pick con lógica real
def sugerir_pick(equipo, form, pitcher, cuota_ml):
    try:
        era = float(pitcher.get("era", 99))
        k = pitcher.get("strikeOuts", 0)
        anotadas = form.get("anotadas", 0)
        if cuota_ml < 1.70 and anotadas >= 4 and era < 3.5:
            return f"🎯 {equipo} ML @ {cuota_ml} | {anotadas}/j, ERA {era}, {k} K"
        elif 1.70 <= cuota_ml <= 2.30 and anotadas >= 4 and era < 4:
            return f"🔥 {equipo} ML @ {cuota_ml} | Valor medio: {anotadas}/j, ERA {era}"
        elif cuota_ml > 2.30 and anotadas >= 4.5 and era < 4.5:
            return f"💥 Sorpresa {equipo} ML @ {cuota_ml} | Underdog con ataque"
    except:
        pass
    return None

# Main
def main():
    print(f"📅 Pronósticos MLB – {HOY}\n")
    try:
        juegos = get_today_games()
        cuotas = get_odds()
    except Exception as e:
        print(f"❌ Error al obtener datos: {e}")
        return

    for j in juegos:
        home, away = j["home"], j["away"]
        form_home = get_team_form(j["home_id"])
        form_away = get_team_form(j["away_id"])
        pitcher_home = get_pitcher_stats(j["pitcher_home"])
        pitcher_away = get_pitcher_stats(j["pitcher_away"])

        match = next((o for o in cuotas if normalize(o["home_team"]) in normalize(home) and normalize(o["away_team"]) in normalize(away)), None)
        if not match:
            continue

        ml = {o["name"]: o["price"] for b in match["bookmakers"] for m in b["markets"] if m["key"] == "h2h" for o in m["outcomes"]}
        cuota_home = ml.get(home)
        cuota_away = ml.get(away)

        print(f"⚔️ {away} @ {home}")
        pick_home = sugerir_pick(home, form_home, pitcher_home, cuota_home) if cuota_home else None
        pick_away = sugerir_pick(away, form_away, pitcher_away, cuota_away) if cuota_away else None

        if pick_home:
            print("🧠", pick_home)
        elif pick_away:
            print("🧠", pick_away)
        else:
            print("⚠️ Sin valor para ML en este juego")
        print("---")

if __name__ == "__main__":
    main()
