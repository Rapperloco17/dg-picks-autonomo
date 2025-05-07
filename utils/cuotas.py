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
        if bookmaker.get("id") == BOOKMAKER_BET365_ID:
            for option in bookmaker.get("bets", []):
                if option.get("name", "").lower() == market.lower():
                    values = option.get("values")
                    if values:
                        cuota = float(values[0].get("odd", 0))
                        return cuota

    # Si no hay Bet365, usar la primera disponible
    for bookmaker in bookmakers:
        for option in bookmaker.get("bets", []):
            if option.get("name", "").lower() == market.lower():
                values = option.get("values")
                if values:
                    cuota = float(values[0].get("odd", 0))
                    return cuota

    return None


