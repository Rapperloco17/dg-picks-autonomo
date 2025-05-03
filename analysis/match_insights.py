import requests
import json
from utils.api_config import API_FOOTBALL_HEADERS

def analizar_fixture(fixture_id):
    # Obtener predicción del API (referencia secundaria)
    pred_url = f"https://v3.football.api-sports.io/predictions?fixture={fixture_id}"
    pred_res = requests.get(pred_url, headers=API_FOOTBALL_HEADERS)
    pred_data = pred_res.json()

    try:
        pred = pred_data['response'][0]['predictions']
        advice = pred_data['response'][0]['advice']
    except (KeyError, IndexError):
        pred, advice = {}, ""

    # Obtener estadísticas reales del fixture
    stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    stats_res = requests.get(stats_url, headers=API_FOOTBALL_HEADERS)
    stats_data = stats_res.json()

    team_stats = {}
    for entry in stats_data.get("response", []):
        team_name = entry['team']['name']
        stats = {stat['type']: stat['value'] for stat in entry['statistics']}
        team_stats[team_name] = stats

    # Cargar fixture
    fixture_url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
    fix_res = requests.get(fixture_url, headers=API_FOOTBALL_HEADERS)
    fix_data = fix_res.json()
    try:
        match = fix_data['response'][0]
    except (KeyError, IndexError):
        return None

    home = match['teams']['home']['name']
    away = match['teams']['away']['name']
    league = match['league']['name']
    date = match['fixture']['date'][:10]

    # --- Análisis real DG Picks ---
    pick = None
    razonamiento = []

    home_stats = team_stats.get(home, {})
    away_stats = team_stats.get(away, {})

    # Goles promedio, tiros, forma
    home_goals = home_stats.get("Goals scored", 0)
    away_goals = away_stats.get("Goals scored", 0)
    home_concede = home_stats.get("Goals conceded", 0)
    away_concede = away_stats.get("Goals conceded", 0)

    if home_goals and away_concede and home_goals >= 1.5 and away_concede >= 1.5:
        razonamiento.append(f"{home} promedia {home_goals} goles a favor y {away} concede {away_concede} por partido.")
        pick = f"{home} gana"

    elif home_goals and away_goals and (home_goals + away_goals) >= 3:
        razonamiento.append(f"Ambos equipos tienen tendencia ofensiva. {home}: {home_goals}, {away}: {away_goals}")
        pick = "Over 2.5 goles"

    elif home_concede and away_concede and (home_concede + away_concede) >= 3:
        razonamiento.append(f"Ambas defensas permiten muchos goles. {home} concede {home_concede}, {away} concede {away_concede}")
        pick = "Ambos anotan (BTTS)"

    # Validación con predicción del API (si coincide)
    if pick and advice and pick.lower() in advice.lower():
        razonamiento.append(f"✔️ El consejo del API también sugiere: '{advice}'")
    elif pick:
        razonamiento.append(f"⚠️ El pick se genera por análisis real, aunque el API no lo recomienda directamente.")

    if not pick:
        return None  # No se detectó valor real

    return {
        "fixture_id": fixture_id,
        "match": f"{home} vs {away}",
        "league": league,
        "fecha": date,
        "pick": pick,
        "razonamiento": razonamiento
    }

