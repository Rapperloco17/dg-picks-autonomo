import requests

API_FOOTBALL_KEY = "178b66e41ba9d4d3b8549f096ef1e377"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}

BASE_URL = "https://v3.football.api-sports.io"


def get_fixtures_today(league_id, season):
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": season,
        "date": __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    }
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("response", [])
    except requests.RequestException as e:
        print(f"❌ Error al consultar liga {league_id}, temporada {season}: {e}")
        return []

def get_team_stats(fixture_id, team_home_id, team_away_id):
    # Esta función es solo un placeholder
    return None

