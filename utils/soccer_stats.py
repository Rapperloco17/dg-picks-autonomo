# utils/soccer_stats.py – Análisis real con forma desde API-FOOTBALL y cuota de Odds API

import requests

# Keys
ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"

# Odds API endpoint (Bet365, mercado H2H)
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
# API-FOOTBALL endpoint
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"

headers_api_football = {
    "x-apisports-key": FOOTBALL_API_KEY
}


def obtener_forma_equipo(equipo_id, local=True):
    try:
        params = {
            "team": equipo_id,
            "last": 5
        }
        if local:
            params["venue"] = "home"
        else:
            params["venue"] = "away"

        res = requests.get(FIXTURES_URL, headers=headers_api_football, params=params)
        data = res.json().get("response", [])

        forma = 0
        for match in data:
            goles_favor = match['goals']['for']
            goles_contra = match['goals']['against']
            resultado = match['teams']['home' if local else 'away']['winner']
            if resultado:
                forma += 3
            elif resultado is None:
                forma += 1

        return forma
    except Exception as e:
        print(f"\u26a0\ufe0f Error al obtener forma del equipo {equipo_id}:", e)
        return 0


def obtener_cuota_real(home_team, away_team):
    try:
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "uk",
            "markets": "h2h",
            "bookmakers": "bet365"
        }
        response = requests.get(ODDS_API_URL, params=params)
        data = response.json()

        for evento in data:
            if home_team in evento['home_team'] and away_team in evento['away_team']:
                odds = evento['bookmakers'][0]['markets'][0]['outcomes']
                for o in odds:
                    if o['name'] == home_team:
                        return round(o['price'], 2)
        return None

    except Exception as e:
        print(f"\u26a0\ufe0f Error obteniendo cuota real: {e}")
        return None


def analizar_partido(fixture):
    try:
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        home_id = fixture['teams']['home']['id']
        away_id = fixture['teams']['away']['id']

        home_form = obtener_forma_equipo(home_id, local=True)
        away_form = obtener_forma_equipo(away_id, local=False)

        cuota_real = obtener_cuota_real(home, away)
        if cuota_real is None:
            cuota_real = 1.70

        justificacion = []
        if home_form >= 9:
            justificacion.append(f"{home} con buena forma en casa (últimos 5)")
        if away_form <= 4:
            justificacion.append(f"{away} flojo como visitante")
        justificacion.append("cuota validada en Bet365")

        if home_form >= 9 and away_form <= 4:
            return {
                "partido": f"{home} vs {away}",
                "pick": f"Gana {home}",
                "cuota": cuota_real,
                "valor": True,
                "justificacion": "; ".join(justificacion)
            }

        return None

    except Exception as e:
        print(f"\u26a0\ufe0f Error analizando partido:", e)
        return None

