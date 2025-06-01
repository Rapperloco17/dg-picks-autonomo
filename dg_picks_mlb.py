import requests
from datetime import datetime, timedelta
import pytz
import os

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

# Mapeo básico de estadios (ajustable con datos reales)
STADIUM_HR_FACTOR = {
    "Fenway Park": 0.7,    # Reduce HR
    "Coors Field": 1.5,    # Aumenta HR
    "Yankee Stadium": 1.2, # Aumenta HR
    "default": 1.0         # Neutro
}

def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
    response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
    data = response.json()
    games = []
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            home_pitcher = game["teams"]["home"].get("probablePitcher", {})
            away_pitcher = game["teams"]["away"].get("probablePitcher", {})
            venue = game["venue"]["name"]
            game_time = datetime.strptime(game["gameDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC).astimezone(MX_TZ).strftime("%I:%M %p CST")
            games.append({
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "away_team_id": game["teams"]["away"]["team"]["id"],
                "game_time": game_time,
                "venue": venue
            })
    return games

def get_pitcher_name(pitcher_id):
    if not pitcher_id:
        return "N/A"
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if not data.get("people"):
        return "N/A"
    return data["people"][0]["fullName"]

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
    # Extraer HR permitidos (home runs allowed)
    hr_allowed = stats.get("homeRunsPer9", 0) or stats.get("homeRuns", 0) / (stats.get("inningsPitched", 1) / 9) if stats.get("inningsPitched") else 0
    stats["hr_allowed_per_game"] = round(hr_allowed, 2)
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
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    response = requests.get(url, headers=HEADERS)
    games = response.json().get("dates", [])
    resultados = []
    hr_hit = 0
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
                hr_hit += game.get("linescore", {}).get("home", {}).get("homeRuns", 0)
            else:
                anotadas = away["score"]
                recibidas = home["score"]
                victoria = anotadas > recibidas
                hr_hit += game.get("linescore", {}).get("away", {}).get("homeRuns", 0)
            resultados.append((anotadas, recibidas, victoria))
    ultimos = resultados[-10:]
    if not ultimos:
        return {}
    promedio_anotadas = round(sum(x[0] for x in ultimos) / len(ultimos), 2)
    promedio_recibidas = round(sum(x[1] for x in ultimos) / len(ultimos), 2)
    victorias = sum(1 for x in ultimos if x[2])
    hr_rate = round((hr_hit / 10) * 100, 2) if ultimos else 0  # % de juegos con HR
    form = {
        "anotadas": promedio_anotadas,
        "recibidas": promedio_recibidas,
        "record": f"{victorias}G-{10 - victorias}P",
        "hr_rate": hr_rate  # Porcentaje de juegos con HR
    }
    return form

def sugerir_pick(equipo, form_eq, pitcher_eq, cuota_ml=None, cuota_spread=None):
    era = float(pitcher_eq.get("era", "99") if pitcher_eq.get("era") else 99)
    anotadas = form_eq.get("anotadas", 0)
    hr_rate = form_eq.get("hr_rate", 0)
    hr_allowed = pitcher_eq.get("hr_allowed_per_game", 0)
    record = form_eq.get("record", "-")

    print(f"🔍 Evaluando pick para {equipo}: ERA={era}, Anotadas={anotadas}, HR Rate={hr_rate}%, HR Allowed={hr_allowed}/juego, Record={record}")

    if era >= 99 or anotadas == 0:
        return f"⚠️ Datos insuficientes para {equipo} (ERA o anotadas no disponibles)"

    # Calcular probabilidad de "no HR"
    no_hr_prob = 100 - hr_rate  # Base: inverso del % de juegos con HR
    no_hr_prob -= (hr_allowed * 10)  # Ajuste por HR permitidos por juego
    no_hr_prob -= (anotadas * 5)  # Ajuste por ofensiva (más carreras = más HR)
    if era < 3.5:
        no_hr_prob += 15  # Bonus por buen pitcheo
    no_hr_prob = max(0, min(100, no_hr_prob))  # Limitar entre 0 y 100

    picks = []
    if cuota_ml is None and cuota_spread is None:
        if anotadas >= 4.0 and era < 4.0:
            picks.append(f"🎯 ¡A por {equipo} ML! | Potente ofensiva ({anotadas}/juego) y pitcher en forma (ERA {era})")
        elif anotadas >= 4.5 and era < 3.7:
            picks.append(f"🔥 {equipo} -1.5, ¡a ganar por más! | Ofensiva explosiva y ERA top (ERA {era})")
        elif anotadas >= 4.5:
            picks.append(f"⚡ {equipo} anota a lo grande ({anotadas}/juego), ¡considera Over!")
        else:
            picks.append(f"👍 {equipo} ML, ¡apuesta segura! | Forma sólida ({record}) y ofensiva decente ({anotadas}/juego)")
    else:
        if cuota_ml and cuota_ml < 1.70 and anotadas >= 3.5 and era < 4.0:
            picks.append(f"🎯 ¡A por {equipo} ML @ {cuota_ml}! | Cuota ideal para parlay, ERA {era}, y {anotadas}/juego")
        elif cuota_ml and 1.70 <= cuota_ml <= 2.50 and anotadas >= 3.5 and era < 4.5:
            picks.append(f"🔥 {equipo} ML @ {cuota_ml}, ¡a darlo todo! | Pitcher estable y ofensiva activa ({anotadas}/juego)")
        elif cuota_ml and cuota_ml > 2.50 and anotadas >= 4.5 and era < 4.2:
            picks.append(f"💥 ¡Sorpresa con {equipo} ML @ {cuota_ml}! | Underdog con valor, anota {anotadas}/juego")
        elif cuota_spread and cuota_ml < 1.70 and anotadas >= 4.5 and era < 3.7:
            picks.append(f"🔥 {equipo} -1.5 @ {cuota_spread}, ¡dominación asegurada! | Ofensiva y ERA top")
        elif anotadas >= 4.5:
            picks.append(f"⚡ {equipo} anota a lo grande ({anotadas}/juego), ¡ve por el Over!")

    # Sugerir "no HR" si la probabilidad es alta
    if no_hr_prob > 60:
        picks.append(f"🌙 Probabilidad de no HR: {no_hr_prob}% | Pitcheo sólido y ofensiva limitada")

    return picks[0] if picks else "⚠️ Partido reñido, ¡evalúa con cuidado!"

def main():
    print("🔍 Analizando partidos de MLB...")
    games = get_today_mlb_games()
    odds = get_odds_for_mlb()

    if not games:
        print("⚠️ No hay juegos programados para hoy.")
        return

    print(f"🔍 Total de juegos encontrados: {len(games)}")
    for idx, game in enumerate(games):
        print(f"\n🎮 Juego {idx + 1}/{len(games)} 🎮")
        home = game['home_team']
        away = game['away_team']
        pitcher_home_id = game['home_pitcher_id']
        pitcher_away_id = game['away_pitcher_id']
        home_team_id = game['home_team_id']
        away_team_id = game['away_team_id']
        game_time = game['game_time']
        venue = game['venue']

        pitcher_home = get_pitcher_stats(pitcher_home_id)
        pitcher_away = get_pitcher_stats(pitcher_away_id)
        form_home = get_team_form(home_team_id)
        form_away = get_team_form(away_team_id)
        pitcher_home_name = get_pitcher_name(pitcher_home_id)
        pitcher_away_name = get_pitcher_name(pitcher_away_id)

        matched = False
        home_normalized = normalize_team(home)
        away_normalized = normalize_team(away)
        print(f"🔍 Equipos normalizados (MLB Stats): {home_normalized} vs {away_normalized}")

        for odd in odds:
            odd_home = normalize_team(odd.get("home_team", ""))
            odd_away = normalize_team(odd.get("away_team", ""))
            print(f"⚠️ Revisando (Odds API): {odd_home} vs {odd_away}")

            if (home_normalized == odd_home and away_normalized == odd_away) or \
               (home_normalized == odd_away and away_normalized == odd_home):

                matched = True
                cuotas = {}
                spreads = {}
                over_line = None
                over_price = None
                under_price = None

                for bookmaker in odd.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "h2h":
                            for o in market["outcomes"]:
                                team = o["name"]
                                price = o["price"]
                                if team not in cuotas or price > cuotas[team]:
                                    cuotas[team] = price
                        elif market["key"] == "spreads":
                            for o in market["outcomes"]:
                                team = o["name"]
                                point = o.get("point")
                                price = o.get("price")
                                if team not in spreads or price > spreads[team][1]:
                                    spreads[team] = (point, price)
                        elif market["key"] == "totals":
                            for o in market["outcomes"]:
                                name = o["name"].lower()
                                point = o.get("point")
                                price = o.get("price")
                                if name == "over" and (over_price is None or price > over_price):
                                    over_line = point
                                    over_price = price
                                elif name == "under" and (under_price is None or price > under_price):
                                    under_price = price

                print(f"🧾 {away} vs {home} | Horario: {game_time} ⏰ | Estadio: {venue}")
                print(f"   ⚾ Pitchers: {pitcher_away_name} ({away}) vs {pitcher_home_name} ({home})")
                print(f"   💰 ML: {away} @ {cuotas.get(away, 'N/A')} | {home} @ {cuotas.get(home, 'N/A')}")
                print(f"   📏 Run Line: {away} {spreads.get(away, ('N/A', 'N/A'))[0]} @ {spreads.get(away, ('N/A', 'N/A'))[1]} | {home} {spreads.get(home, ('N/A', 'N/A'))[0]} @ {spreads.get(home, ('N/A', 'N/A'))[1]}")
                print(f"   🔢 Over/Under: O{over_line} @ {over_price} | U{over_line} @ {under_price}")
                print(f"   📊 ERA Pitchers: {pitcher_away.get('era', '❌')} vs {pitcher_home.get('era', '❌')}")
                print(f"   📅 Forma (últ 10): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
                print(f"   📈 Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
                total_combinado = (
                    form_home.get("anotadas", 0) + form_home.get("recibidas", 0) +
                    form_away.get("anotadas", 0) + form_away.get("recibidas", 0)
                ) / 2
                stadium_factor = STADIUM_HR_FACTOR.get(venue, STADIUM_HR_FACTOR["default"])
                print(f"   🎯 Total estimado: {round(total_combinado, 2)} carreras | Factor estadio: {stadium_factor}x")

                ventaja_home = form_home.get("anotadas", 0) > form_away.get("anotadas", 0) and \
                               float(pitcher_home.get("era", 99)) < float(pitcher_away.get("era", 99))
                ventaja_away = form_away.get("anotadas", 0) > form_home.get("anotadas", 0) and \
                               float(pitcher_away.get("era", 99)) < float(pitcher_home.get("era", 99))

                if ventaja_home and not ventaja_away:
                    pick_home = sugerir_pick(home, form_home, pitcher_home, cuotas.get(home), spreads.get(home, (None, None))[1])
                    print("   🧠", pick_home)
                elif ventaja_away and not ventaja_home:
                    pick_away = sugerir_pick(away, form_away, pitcher_away, cuotas.get(away), spreads.get(away, (None, None))[1])
                    print("   🧠", pick_away)
                else:
                    pick_home = sugerir_pick(home, form_home, pitcher_home, cuotas.get(home), spreads.get(home, (None, None))[1])
                    pick_away = sugerir_pick(away, form_away, pitcher_away, cuotas.get(away), spreads.get(away, (None, None))[1])
                    print("   🧠", pick_home if form_home.get("anotadas", 0) >= form_away.get("anotadas", 0) else pick_away)
                break

        if not matched:
            print(f"🧾 {away} vs {home} (sin cuotas) | Horario: {game_time} ⏰ | Estadio: {venue}")
            print(f"   ⚾ Pitchers: {pitcher_away_name} ({away}) vs {pitcher_home_name} ({home})")
            print(f"   ⚠️ No se encontraron cuotas para este partido")
            print(f"   📊 ERA Pitchers: {pitcher_away.get('era', '❌')} vs {pitcher_home.get('era', '❌')}")
            print(f"   📅 Forma (últ 10): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
            print(f"   📈 Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
            total_combinado = (
                form_home.get("anotadas", 0) + form_home.get("recibidas", 0) +
                form_away.get("anotadas", 0) + form_away.get("recibidas", 0)
            ) / 2
            stadium_factor = STADIUM_HR_FACTOR.get(venue, STADIUM_HR_FACTOR["default"])
            print(f"   🎯 Total estimado: {round(total_combinado, 2)} carreras | Factor estadio: {stadium_factor}x")

            pick_home = sugerir_pick(home, form_home, pitcher_home)
            pick_away = sugerir_pick(away, form_away, pitcher_away)
            print("   🧠", pick_home if form_home.get("anotadas", 0) >= form_away.get("anotadas", 0) else pick_away)

    print("\n✅ Análisis completo")

if __name__ == "__main__":
    main()
