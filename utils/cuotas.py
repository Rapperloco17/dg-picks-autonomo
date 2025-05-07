import requests
from utils.api_football import HEADERS, BASE_URL

BOOKMAKER_BET365_ID = 6


def obtener_cuota_fixture(fixture_id, market):
    url = f"{BASE_URL}/odds"
    params = {
        "fixture": fixture_id,
        "market": market
    }
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    if not data.get("response"):
        return None

    odds_data = data["response"][0]
    bookmakers = odds_data.get("bookmakers", [])

    cuota = None

    # Intentar primero con Bet365 si está disponible
    for bookmaker in bookmakers:
        if bookmaker["id"] == BOOKMAKER_BET365_ID:
            for option in bookmaker["bets"]:
                if option["name"].lower() == market.lower():
                    if option["values"]:
                        cuota = float(option["values"][0]["odd"])
                        return cuota

    # Si no hay Bet365, usar la primera disponible
    for bookmaker in bookmakers:
        for option in bookmaker["bets"]:
            if option["name"].lower() == market.lower():
                if option["values"]:
                    cuota = float(option["values"][0]["odd"])
                    return cuota

    return None

