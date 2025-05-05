import requests

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"


def obtener_partidos_de_liga(liga_id, fecha, temporada):
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha
    }

    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    if data.get("errors"):
        raise Exception(f"API error: {data['errors']}")

    partidos = []
    for item in data.get("response", []):
        fixture = item["fixture"]
        league = item["league"]
        teams = item["teams"]

        partido = {
            "fixture": {
                "id": fixture["id"],
                "date": fixture["date"]
            },
            "league": {
                "id": league["id"],
                "season": league["season"]
            },
            "teams": {
                "home": {"name": teams["home"]["name"], "id": teams["home"]["id"]},
                "away": {"name": teams["away"]["name"], "id": teams["away"]["id"]}
            }
        }

        partidos.append(partido)

    return partidos


def obtener_datos_fixture(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics"
    params = {
        "fixture": fixture_id
    }

    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    if data.get("errors"):
        raise Exception(f"API error: {data['errors']}")

    estadisticas = {}
    for equipo in data.get("response", []):
        team_name = equipo["team"]["name"]
        for stat in equipo.get("statistics", []):
            estadisticas[f"{team_name}_{stat['type']}"] = stat["value"]

    return estadisticas


