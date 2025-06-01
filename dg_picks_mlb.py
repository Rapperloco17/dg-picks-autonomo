import requests

API_KEY = "6d74bb8689679bb5d1c71a18a327a0f9"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

params = {
    "apiKey": API_KEY,
    "regions": "us",  # solo cuotas de casas de EEUU
    "markets": "h2h,spreads,totals",
    "oddsFormat": "decimal"
}

try:
    response = requests.get(ODDS_API_URL, params=params, timeout=10)
    response.raise_for_status()
    odds_data = response.json()

    print(f"\n✅ Se encontraron {len(odds_data)} partidos con cuotas.\n")

    for game in odds_data[:5]:  # Solo muestra los primeros 5 partidos
        print(f"📌 {game['home_team']} vs {game['away_team']}")
        for bookmaker in game.get("bookmakers", []):
            print(f"  🏦 Casa: {bookmaker['title']}")
            for market in bookmaker.get("markets", []):
                print(f"    📊 Mercado: {market['key']}")
                for outcome in market["outcomes"]:
                    print(f"     ➤ {outcome['name']}: {outcome['price']}")
        print("-" * 40)

except Exception as e:
    print("❌ Error al obtener cuotas:", e)
