import os
import requests
import logging
import csv
from datetime import datetime, timedelta
import pytz
from openai import OpenAI

# Configuración de logging
logging.basicConfig(filename='mlb_picks.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Validar variables de entorno
required_env_vars = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "CHAT_ID_VIP", "CHAT_ID_FREE", "ODDS_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Falta la variable de entorno: {var}")
        raise ValueError(f"Falta la variable de entorno: {var}")

# Configuraciones
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
token_telegram = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id_vip = os.getenv("CHAT_ID_VIP")
chat_id_free = os.getenv("CHAT_ID_FREE")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Constantes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

def get_today_mlb_games():
    try:
        params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
        response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
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
    except requests.RequestException as e:
        logging.error(f"Error al obtener juegos de MLB: {e}")
        return []

def get_team_era(team_id):
    try:
        url = MLB_TEAM_STATS_URL.format(team_id)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return float(data["stats"][0]["splits"][0]["stat"].get("era", 4.5))
    except:
        logging.error(f"Error al obtener ERA del equipo ID {team_id}")
        return 4.5

def get_pitcher_stats(pitcher_id, team_id):
    if not pitcher_id:
        return {"era": get_team_era(team_id)}
    try:
        url = MLB_PLAYER_STATS_URL.format(pitcher_id)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        splits = data.get("people", [{}])[0].get("stats", [{}])[0].get("splits", [])
        return splits[0].get("stat", {"era": get_team_era(team_id)}) if splits else {"era": get_team_era(team_id)}
    except requests.RequestException as e:
        logging.error(f"Error al obtener stats del pitcher ID {pitcher_id}: {e}")
        return {"era": get_team_era(team_id)}

def get_team_form(team_id, start_date, end_date):
    try:
        url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
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
    except requests.RequestException as e:
        logging.error(f"Error al obtener forma del equipo ID {team_id}: {e}")
        return {"anotadas": 0, "recibidas": 0}

def get_team_avg(team_id):
    try:
        response = requests.get(MLB_TEAM_STATS_URL.format(team_id), headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return float(data["stats"][0]["splits"][0]["stat"]["battingAvg"])
    except (requests.RequestException, KeyError, ValueError) as e:
        logging.error(f"Error al obtener promedio de bateo del equipo ID {team_id}: {e}")
        return 0.25

def ajustar_por_era(base, era):
    try:
        era = float(era)
        if era

System: I notice you're asking about the importance of historical data for improving your betting script, particularly for moneyline picks. Since your previous question focused on the reliability of the moneyline logic, I’ll address why historical data is critical for ensuring your picks are trustworthy and suggest specific ways to incorporate it into your script. I’ll also include a practical implementation to validate your moneyline picks using historical data, building on the code you provided. Let’s dive in, ¡papi!

---

### Why Historical Data is Important for Your Betting Script

Historical data is crucial for making your **moneyline**, **run line**, and **totals** picks more reliable and profitable. Here’s why it matters and how it directly impacts your script:

1. **Validating Prediction Accuracy**:
   - Historical data lets you test how well your `diferencia_carreras` (for moneyline) and `estimado_total` (for totals) predict actual game outcomes.
   - Example: If your moneyline picks with `abs(diferencia_carreras) >= 1.7` correctly predict the winner 65% of the time, you can trust the threshold. If it’s only 50%, you need to adjust it.

2. **Optimizing Thresholds**:
   - The current thresholds (1.7 for "normal" and 2.7 for "candado" moneyline picks) are guesses. Historical data helps you find the optimal values that maximize wins or profits.
   - Example: Testing might show that `abs(diferencia_carreras) >= 2.0` yields a 70% win rate, better than 1.7.

3. **Identifying Team and Context Trends**:
   - Historical data reveals patterns, like teams performing better at home, against specific pitchers, or in certain stadiums.
   - Example: The Yankees might win 80% of home games against teams with pitchers who have an ERA > 4.0.

4. **Assessing Profitability**:
   - By comparing your picks’ odds with actual results, you can calculate the return on investment (ROI). This ensures your strategy is financially sound.
   - Example: A moneyline pick at 1.80 odds needs to win at least 55.6% of the time to break even.

5. **Refining the Model**:
   - Historical data lets you test additional factors (e.g., home/away splits, bullpen ERA, or head-to-head records) to improve predictions.
   - Example: Adding a home-field advantage adjustment (+0.5 to `diferencia_carreras`) might boost accuracy.

6. **Avoiding Overfitting or Bias**:
   - Without historical data, you might rely on a model that seems logical but fails in practice (e.g., overestimating ERA’s impact). Historical data grounds your strategy in real outcomes.

**Bottom Line**: Historical data is like a playbook—it shows you what works, what doesn’t, and how to tweak your script to make smarter, more profitable picks. Without it, you’re betting on untested assumptions.

---

### How to Use Historical Data to Improve Your Script

Here’s a step-by-step plan to integrate historical data into your script, focusing on validating and improving **moneyline** picks (but applicable to run line and totals too):

1. **Collect Historical Game Data**:
   - Use the MLB Stats API (`MLB_RESULTS_URL`) to fetch game results from the past 30 days or the 2024 season.
   - Extract: teams, scores, winner, pitcher IDs, team batting averages, and other stats used in your model.
   - Store in a CSV or SQLite database for easy analysis.

2. **Simulate Picks on Historical Data**:
   - Run your existing logic (e.g., calculate `diferencia_carreras`) on past games to generate hypothetical picks.
   - Compare picks to actual winners to calculate accuracy.

3. **Analyze and Optimize Thresholds**:
   - Test different `diferencia_carreras` thresholds (e.g., 1.5, 1.7, 2.0) to find the one with the highest win rate or ROI.
   - Example: If `abs(diferencia_carreras) >= 2.0` wins 70% of the time vs. 65% for 1.7, update the threshold.

4. **Add Contextual Factors**:
   - Use historical data to test if factors like home/away performance or head-to-head records improve predictions.
   - Example: Add a +0.5 boost to `diferencia_carreras` for home teams and check if it increases accuracy.

5. **Track Ongoing Performance**:
   - Save every pick (with odds, estimated difference, and actual result) to a CSV to monitor long-term performance.
   - Example: `[2025-05-30, "Red Sox vs Yankees", "Moneyline", "Yankees", 1.75, "candado", 2.7, 77.0%, "Win"]`.

6. **Visualize Results**:
   - Create charts to see trends, like how `diferencia_carreras` correlates with wins or how accurate your picks are by team.

---

### Updated Script with Historical Data Validation

Below is an updated version of your script that adds:
- A function to collect historical game data.
- A function to validate moneyline picks using historical data.
- A CSV to store results for analysis.
- Adjusted thresholds based on a hypothetical analysis (you’ll need to run real data to confirm).

This code replaces the `main()` function from your previous script and adds new functions for historical validation. It focuses on moneyline but can be extended to run line and totals.

<xaiArtifact artifact_id="77ce6c8f-68c8-4220-b743-aad737dd4d77" artifact_version_id="03eb7f33-cc76-4368-b90c-c53ce4242fcb" title="mlb_betting_picks.py" contentType="text/python">
import os
import requests
import logging
import csv
from datetime import datetime, timedelta
import pytz
from openai import OpenAI

# Configuración de logging
logging.basicConfig(filename='mlb_picks.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Validar variables de entorno
required_env_vars = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "CHAT_ID_VIP", "CHAT_ID_FREE", "ODDS_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Falta la variable de entorno: {var}")
        raise ValueError(f"Falta la variable de entorno: {var}")

# Configuraciones
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
token_telegram = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id_vip = os.getenv("CHAT_ID_VIP")
chat_id_free = os.getenv("CHAT_ID_FREE")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Constantes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={}&endDate={}&hydrate=team,linescore,probablePitcher"
HEADERS = {"User-Agent": "DG Picks"}
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

def get_team_era(team_id):
    try:
        url = MLB_TEAM_STATS_URL.format(team_id)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return float(data["stats"][0]["splits"][0]["stat"].get("era", 4.5))
    except:
        logging.error(f"Error al obtener ERA del equipo ID {team_id}")
        return 4.5

def get_pitcher_stats(pitcher_id, team_id):
    if not pitcher_id:
        return {"era": get_team_era(team_id)}
    try:
        url = MLB_PLAYER_STATS_URL.format(pitcher_id)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        splits = data.get("people", [{}])[0].get("stats", [{}])[0].get("splits", [])
        return splits[0].get("stat", {"era": get_team_era(team_id)}) if splits else {"era": get_team_era(team_id)}
    except requests.RequestException as e:
        logging.error(f"Error al obtener stats del pitcher ID {pitcher_id}: {e}")
        return {"era": get_team_era(team_id)}

def get_team_form(team_id, start_date, end_date):
    try:
        url = MLB_RESULTS_URL.format(start_date, end_date)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        resultados = []
        for fecha in data.get("dates", []):
            for game in fecha.get("games", []):
                if game.get("status", {}).get("detailedState") != "Final" or team_id not in [game["teams"]["home"]["team"]["id"], game["teams"]["away"]["team"]["id"]]:
                    continue
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
    except requests.RequestException as e:
        logging.error(f"Error al obtener forma del equipo ID {team_id}: {e}")
        return {"anotadas": 0, "recibidas": 0}

def get_team_avg(team_id):
    try:
        response = requests.get(MLB_TEAM_STATS_URL.format(team_id), headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return float(data["stats"][0]["splits"][0]["stat"]["battingAvg"])
    except (requests.RequestException, KeyError, ValueError) as e:
        logging.error(f"Error al obtener promedio de bateo del equipo ID {team_id}: {e}")
        return 0.25

def ajustar_por_era(base, era):
    try:
        era = float(era)
        if era < 2.5: return base - 0.7
        elif era < 3.5: return base - 0.3
        elif era < 4.5: return base
        elif era < 5.5: return base + 0.5
        else: return base + 0.8
    except ValueError:
        return base

def ajustar_por_avg(base, avg):
    try:
        if avg < 0.230: return base - 0.5
        elif avg < 0.250: return base - 0.2
        elif avg < 0.270: return base
        elif avg < 0.290: return base + 0.3
        else: return base + 0.6
    except TypeError:
        return base

def get_odds(date=HOY):
    try:
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal",
            "date": date
        }
        response = requests.get(ODDS_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error al obtener cuotas: {e}")
        return []

def generar_mensaje_ia(partido, pick, cuota, linea, estimado, mercado):
    try:
        prompt = f"""Genera un mensaje estilo canal premium de apuestas para Telegram.
        Partido: {partido}
        Mercado: {mercado}
        Pick: {pick} @ {cuota} | Línea: {linea} | Estimado: {estimado}.
        No menciones IA ni OpenAI. Termina con '✅ Valor detectado en la cuota'."""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error al generar mensaje con OpenAI: {e}")
        return f"Partido: {partido}\nMercado: {mercado}\nPick: {pick} @ {cuota} | Línea: {linea} | Estimado: {estimado}\n✅ Valor detectado en la cuota"

def enviar_a_telegram(mensaje, tipo):
    destino = chat_id_vip if tipo == "candado" else chat_id_free
    url = f"https://api.telegram.org/bot{token_telegram}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": destino, "text": mensaje, "parse_mode": "HTML"})
        response.raise_for_status()
        logging.info(f"Mensaje enviado a Telegram ({tipo}): {mensaje[:50]}...")
    except requests.RequestException as e:
        logging.error(f"Error al enviar a Telegram: {e}")

def get_historical_games(start_date, end_date):
    try:
        params = {"sportId": 1, "startDate": start_date, "endDate": end_date, "hydrate": "team,linescore,probablePitcher"}
        response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        games = []
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                if game.get("status", {}).get("detailedState") != "Final": continue
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                winner = home["team"]["name"] if home["score"] > away["score"] else away["team"]["name"]
                games.append({
                    "date": date_info["date"],
                    "home_team": home["team"]["name"],
                    "away_team": away["team"]["name"],
                    "home_team_id": home["team"]["id"],
                    "away_team_id": away["team"]["id"],
                    "home_pitcher_id": home.get("probablePitcher", {}).get("id"),
                    "away_pitcher_id": away.get("probablePitcher", {}).get("id"),
                    "home_score": home["score"],
                    "away_score": away["score"],
                    "winner": winner
                })
        return games
    except requests.RequestException as e:
        logging.error(f"Error al obtener juegos históricos: {e}")
        return []

def validate_historical_picks():
    # Obtener juegos de los últimos 30 días
    end_date = datetime.now(MX_TZ) - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    games = get_historical_games(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    results = []
    for game in games:
        home = game["home_team"]
        away = game["away_team"]
        partido = f"{away} vs {home}"
        form_home = get_team_form(game["home_team_id"], (datetime.strptime(game["date"], "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d"), game["date"])
        form_away = get_team_form(game["away_team_id"], (datetime.strptime(game["date"], "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d"), game["date"])
        avg_home = get_team_avg(game["home_team_id"])
        avg_away = get_team_avg(game["away_team_id"])
        era_home = float(get_pitcher_stats(game["home_pitcher_id"], game["home_team_id"]).get("era", 4.5))
        era_away = float(get_pitcher_stats(game["away_pitcher_id"], game["away_team_id"]).get("era", 4.5))

        ajustado_home = ajustar_por_avg(ajustar_por_era(form_home["anotadas"], era_away), avg_home)
        ajustado_away = ajustar_por_avg(ajustar_por_era(form_away["anotadas"], era_home), avg_away)
        diferencia_carreras = ajustado_home - ajustado_away + 0.5  # Bonus por jugar en casa
        probabilidad = max(10, min(90, 50 + (diferencia_carreras * 10)))

        pick = None
        tipo = None
        if abs(diferencia_carreras) >= 1.7:
            pick = home if diferencia_carreras > 0 else away
            tipo = "candado" if abs(diferencia_carreras) >= 2.7 else "normal"
        
        if pick:
            acierto = pick == game["winner"]
            results.append({
                "date": game["date"],
                "partido": partido,
                "pick": pick,
                "tipo": tipo,
                "diferencia_carreras": diferencia_carreras,
                "probabilidad": probabilidad,
                "acierto": acierto,
                "winner": game["winner"]
            })
            logging.info(f"Validación: {partido} | Pick: {pick} ({tipo}) | Dif: {diferencia_carreras:.2f} | Prob: {probabilidad:.1f}% | Acierto: {acierto}")

    # Guardar resultados en CSV
    with open('historical_validation.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Partido", "Pick", "Tipo", "Diferencia_Carreras", "Probabilidad", "Acierto", "Ganador"])
        for result in results:
            writer.writerow([result["date"], result["partido"], result["pick"], result["tipo"], 
                            result["diferencia_carreras"], result["probabilidad"], result["acierto"], result["winner"]])

    # Calcular tasa de aciertos
    if results:
        aciertos = sum(1 for r in results if r["acierto"])
        tasa_aciertos = (aciertos / len(results)) * 100
        logging.info(f"Tasa de aciertos (Moneyline): {tasa_aciertos:.1f}% ({aciertos}/{len(results)})")
        return tasa_aciertos
    return 0

def main():
    logging.info("🔍 Ejecutando DG Picks MLB completo")
    
    # Validar modelo con datos históricos (opcional, descomentar para ejecutar)
    # tasa_aciertos = validate_historical_picks()
    # logging.info(f"Validación histórica completada. Tasa de aciertos: {tasa_aciertos:.1f}%")
    
    juegos = get_today_mlb_games()
    odds = get_odds()
    picks_enviados = {"h2h": 0, "spreads": 0, "totals": 0}

    for juego in juegos:
        home = juego["home_team"]
        away = juego["away_team"]
        partido = f"{away} vs {home}"
        form_home = get_team_form(juego["home_team_id"], (datetime.now(MX_TZ) - timedelta(days=10)).strftime("%Y-%m-%d"), HOY)
        form_away = get_team_form(juego["away_team_id"], (datetime.now(MX_TZ) - timedelta(days=10)).strftime("%Y-%m-%d"), HOY)
        avg_home = get_team_avg(juego["home_team_id"])
        avg_away = get_team_avg(juego["away_team_id"])
        era_home = float(get_pitcher_stats(juego["home_pitcher_id"], juego["home_team_id"]).get("era", 4.5))
        era_away = float(get_pitcher_stats(juego["away_pitcher_id"], juego["away_team_id"]).get("era", 4.5))

        ajustado_home = ajustar_por_avg(ajustar_por_era(form_home["anotadas"], era_away), avg_home)
        ajustado_away = ajustar_por_avg(ajustar_por_era(form_away["anotadas"], era_home), avg_away)
        estimado_total = round((ajustado_home + ajustado_away + form_home["recibidas"] + form_away["recibidas"]) / 2, 2)
        diferencia_carreras = ajustado_home - ajustado_away + 0.5  # Bonus por jugar en casa
        probabilidad = max(10, min(90, 50 + (diferencia_carreras * 10)))

        logging.info(f"Juego: {partido}, Ajustado Home: {ajustado_home}, Ajustado Away: {ajustado_away}, Estimado Total: {estimado_total}, Dif Carreras: {diferencia_carreras}, Prob: {probabilidad:.1f}%")

        for odd in odds:
            if (juego["home_team_id"] == odd.get("home_team_id", 0) or 
                juego["away_team_id"] == odd.get("away_team_id", 0) or
                (home.lower() == odd.get("home_team", "").lower() and 
                 away.lower() == odd.get("away_team", "").lower())):
                
                for market in odd.get("bookmakers", [{}])[0].get("markets", []):
                    if market["key"] == "totals" and picks_enviados["totals"] < 3:
                        best_odds = max(
                            (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker["markets"][0]["outcomes"]),
                            key=lambda x: x["price"] if x["name"].lower() == "over" else -x["price"]
                        )
                        linea = best_odds["point"]
                        cuota = best_odds["price"]
                        diferencia = estimado_total - linea
                        if abs(diferencia) >= 2:
                            tipo = "candado" if abs(diferencia) >= 3 else "normal"
                            pick = "Over" if diferencia > 0 else "Under"
                            mensaje = generar_mensaje_ia(partido, f"{pick} {linea}", cuota, linea, f"{estimado_total} carreras", "Totals")
                            enviar_a_telegram(mensaje, tipo)
                            logging.info(f"Pick Totals: {pick} {linea} @ {cuota} ({tipo}) | {partido}")
                            picks_enviados["totals"] += 1

                    if market["key"] == "h2h" and picks_enviados["h2h"] < 2:
                        best_odds = max(
                            (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker.get("markets", []) 
                             if bookmaker["markets"][0]["key"] == "h2h" for outcome in bookmaker["markets"][0]["outcomes"]),
                            key=lambda x: x["price"]
                        )
                        if abs(diferencia_carreras) >= 1.7:
                            pick = home if diferencia_carreras > 0 else away
                            cuota = next((o["price"] for o in market["outcomes"] if o["name"] == pick), 1.0)
                            tipo = "candado" if abs(diferencia_carreras) >= 2.7 else "normal"
                            mensaje = generar_mensaje_ia(partido, f"{pick}", cuota, "N/A", f"{diferencia_carreras:+.2f} carreras ventaja | Prob: {probabilidad:.1f}%", "Moneyline")
                            enviar_a_telegram(mensaje, tipo)
                            logging.info(f"Pick Moneyline: {pick} @ {cuota} ({tipo}) | {partido} | Prob: {probabilidad:.1f}%")
                            picks_enviados["h2h"] += 1
                            with open('picks_history.csv', 'a', newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow([HOY, partido, "Moneyline", pick, cuota, tipo, diferencia_carreras, probabilidad])

                    if market["key"] == "spreads" and picks_enviados["spreads"] < 2:
                        best_odds = max(
                            (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker.get("markets", []) 
                             if bookmaker["markets"][0]["key"] == "spreads" for outcome in bookmaker["markets"][0]["outcomes"]),
                            key=lambda x: x["price"]
                        )
                        linea = best_odds["point"]
                        cuota = best_odds["price"]
                        pick_team = home if diferencia_carreras > 0 else away
                        if abs(diferencia_carreras) >= 2:
                            tipo = "
