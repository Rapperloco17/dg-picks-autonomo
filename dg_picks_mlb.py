import requests
from datetime import datetime, timedelta
import pytz

ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = "2025-05-31"

def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
    data = response.json()
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

def get_odds_for_mlb():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    try:
        response = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
        odds_data = response.json()
        if isinstance(odds_data, list):
            return odds_data
        return []
    except:
        return []

def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if not data.get("people") or not data["people"][0].get("stats"):
        return {}
    splits = data["people"][0]["stats"][0].get("splits", [])
    stats = splits[0].get("stat", {}) if splits else {}
    return stats

def get_team_stats(team_id):
    url = MLB_TEAM_STATS_URL.format(team_id)
    response = requests.get(url, headers=HEADERS)
    stats = response.json()
    if not stats.get("stats") or not stats["stats"][0].get("splits"):
        return {}
    return stats["stats"][0]["splits"][0].get("stat", {})

def get_team_form(team_id):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    response = requests.get(url, headers=HEADERS)
    games = response.json().get("dates", [])
    resultados = []
    for fecha in games:
        for game in fecha.get("games", []):
            if game.get("status", {}).get("detailedState") != "Final":
                continue
            home = game["teams"]["home"]
            away = game["teams"]["away"]
            if home["team"]["id"] == team_id:
                anotadas = home["score"]
                recibidas = away["score"]
                victoria = anotadas > recibidas
            else:
                anotadas = away["score"]
                recibidas = home["score"]
                victoria = anotadas > recibidas
            resultados.append((anotadas, recibidas, victoria))
    ultimos = resultados[-5:]
    if not ultimos:
        return {}
    promedio_anotadas = round(sum(x[0] for x in ultimos) / len(ultimos), 2)
    promedio_recibidas = round(sum(x[1] for x in ultimos) / len(ultimos), 2)
    victorias = sum(1 for x in ultimos if x[2])
    form = {
        "anotadas": promedio_anotadas,
        "recibidas": promedio_recibidas,
        "record": f"{victorias}G-{5 - victorias}P"
    }
    return form

def sugerir_pick(equipo, form_eq, pitcher_eq, cuota_ml=None, cuota_spread=None):
    try:
        era = float(pitcher_eq.get("era", 99))
        anotadas = form_eq.get("anotadas", 0)
        record = form_eq.get("record", "-")

        # Si no hay cuotas, usamos solo ERA y forma reciente
        if cuota_ml is None and cuota_spread is None:
            if anotadas >= 4.0 and era < 4.0:
                return f"✅ {equipo} ML (sin cuota) | Motivo: buena ofensiva ({anotadas}/juego) y pitcher sólido (ERA {era})"
            elif anotadas >= 4.5 and era < 3.7:
                return f"✅ {equipo} -1.5 (sin cuota) | Motivo: ofensiva encendida y ERA dominante"
            elif anotadas >= 4.5:
                return f"⚠️ {equipo} anota mucho ({anotadas}/juego), considerar Over"
            else:
                return "⚠️ Partido parejo o sin valor claro"

        # Lógica con cuotas
        if cuota_ml and cuota_ml < 1.70 and anotadas >= 3.5 and era < 4.0:
            return f"✅ {equipo} ML @ {cuota_ml} | Motivo: cuota baja ideal para parlay, ERA {era}, anotadas {anotadas}/juego"
        elif cuota_ml and 1.70 <= cuota_ml <= 2.50 and anotadas >= 3.5 and era < 4.5:
            return f"✅ {equipo} ML @ {cuota_ml} | Motivo: pitcher aceptable y ofensiva activa ({anotadas}/juego)"
        elif cuota_ml and cuota_ml > 2.50 and anotadas >= 4.5 and era < 4.2:
            return f"🔥 Underdog con valor: {equipo} ML @ {cuota_ml} – Anota {anotadas}/juego, ERA decente"
        elif cuota_spread and cuota_ml < 1.70 and anotadas >= 4.5 and era < 3.7:
            return f"✅ {equipo} -1.5 @ {cuota_spread} | Motivo: ofensiva encendida + ERA dominante"
        elif anotadas >= 4.5:
            return f"⚠️ {equipo} anota mucho ({anotadas}/juego), considerar Over"
        else:
            return "⚠️ Partido parejo o sin valor claro"
    except:
        return "❌ Sin datos para sugerir pick"

def main():
    print("🔍 Analizando partidos de MLB...")
    games = get_today_mlb_games()
    odds = get_odds_for_mlb()

    for game in games:
        home = game['home_team']
        away = game['away_team']
        pitcher_home = get_pitcher_stats(game['home_pitcher_id'])
        pitcher_away = get_pitcher_stats(game['away_pitcher_id'])
        form_home = get_team_form(game['home_team_id'])
        form_away = get_team_form(game['away_team_id'])

        matched = False
        if odds:  # Solo intentamos emparejar si hay cuotas
            for odd in odds:
                if matched:
                    break
                if isinstance(odd, dict):
                    home_match = home.lower().replace(" ", "") in odd["home_team"].lower().replace(" ", "")
                    away_match = away.lower().replace(" ", "") in odd["away_team"].lower().replace(" ", "")
                    if home_match and away_match:
                        matched = True
                        cuotas = {}
                        spreads = {}
                        over_line = None
                        over_price = None
                        under_price = None
                        for m in odd["bookmakers"][0]["markets"]:
                            if m["key"] == "h2h":
                                for o in m["outcomes"]:
                                    cuotas[o["name"]] = o["price"]
                            if m["key"] == "spreads":
                                for o in m["outcomes"]:
                                    spreads[o["name"]] = (o["point"], o["price"])
                            if m["key"] == "totals":
                                for o in m["outcomes"]:
                                    if o["name"].lower() == "over":
                                        over_line = o["point"]
                                        over_price = o["price"]
                                    if o["name"].lower() == "under":
                                        under_price = o["price"]

                        print(f"\n🧾 {away} vs {home}")
                        print(f"   ML: {away} @ {cuotas.get(away, 'N/A')} | {home} @ {cuotas.get(home, 'N/A')}")
                        print(f"   Run Line: {away} {spreads.get(away, ('N/A', 'N/A'))[0]} @ {spreads.get(away, ('N/A', 'N/A'))[1]} | {home} {spreads.get(home, ('N/A', 'N/A'))[0]} @ {spreads.get(home, ('N/A', 'N/A'))[1]}")
                        print(f"   Over/Under: O{over_line} @ {over_price} | U{over_line} @ {under_price}")
                        print(f"   ERA Pitchers: {pitcher_away.get('era', '❌')} vs {pitcher_home.get('era', '❌')}")
                        print(f"   Forma (últ 5): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
                        print(f"   Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
                        total_combinado = (
                            form_home.get("anotadas", 0) + form_home.get("recibidas", 0) +
                            form_away.get("anotadas", 0) + form_away.get("recibidas", 0)
                        ) / 2
                        print(f"   Total estimado: {round(total_combinado, 2)} carreras")

                        anotadas_home = form_home.get("anotadas", 0)
                        anotadas_away = form_away.get("anotadas", 0)
                        era_home = float(pitcher_home.get("era", 99))
                        era_away = float(pitcher_away.get("era", 99))

                        ventaja_home = anotadas_home > anotadas_away and era_home < era_away
                        ventaja_away = anotadas_away > anotadas_home and era_away < era_home

                        if ventaja_home and not ventaja_away:
                            pick_home = sugerir_pick(home, form_home, pitcher_home, cuotas.get(home), spreads.get(home, (None, None))[1])
                            print("   🧠", pick_home)
                        elif ventaja_away and not ventaja_home:
                            pick_away = sugerir_pick(away, form_away, pitcher_away, cuotas.get(away), spreads.get(away, (None, None))[1])
                            print("   🧠", pick_away)
                        else:
                            print("   ⚠️ Partido parejo o sin ventaja clara")

        if not matched:  # Sin cuotas, generamos picks basados solo en estadísticas
            print(f"\n🧾 {away} vs {home} (sin cuotas)")
            print(f"   ERA Pitchers: {pitcher_away.get('era', '❌')} vs {pitcher_home.get('era', '❌')}")
            print(f"   Forma (últ 5): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
            print(f"   Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
            total_combinado = (
                form_home.get("anotadas", 0) + form_home.get("recibidas", 0) +
                form_away.get("anotadas", 0) + form_away.get("recibidas", 0)
            ) / 2
            print(f"   Total estimado: {round(total_combinado, 2)} carreras")

            anotadas_home = form_home.get("anotadas", 0)
            anotadas_away = form_away.get("anotadas", 0)
            era_home = float(pitcher_home.get("era", 99))
            era_away = float(pitcher_away.get("era", 99))

            ventaja_home = anotadas_home > anotadas_away and era_home < era_away
            ventaja_away = anotadas_away > anotadas_home and era_away < era_home

            if ventaja_home and not ventaja_away:
                pick_home = sugerir_pick(home, form_home, pitcher_home)
                print("   🧠", pick_home)
            elif ventaja_away and not ventaja_home:
                pick_away = sugerir_pick(away, form_away, pitcher_away)
                print("   🧠", pick_away)
            else:
                print("   ⚠️ Partido parejo o sin ventaja clara")

    print("\n✅ Análisis completo")

if __name__ == "__main__":
    main()
