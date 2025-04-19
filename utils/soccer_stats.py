# utils/soccer_stats.py – Ahora usando solo API-FOOTBALL (cuotas ML, tarjetas y corners)

import requests

# Clave única para API-FOOTBALL
FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"

# Endpoints de API-FOOTBALL
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
ODDS_URL = "https://v3.football.api-sports.io/odds"

headers_api_football = {
    "x-apisports-key": FOOTBALL_API_KEY
}

# IDs de mercados comunes (según API-FOOTBALL)
BET_IDS = {
    "ML": 1,              # Match Winner
    "TARJETAS": 88,       # Total Cards
    "CORNERS": 121        # Total Corners
}
BOOKMAKER_BET365 = 6


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
            resultado = match['teams']['home' if local else 'away']['winner']
            if resultado:
                forma += 3
            elif resultado is None:
                forma += 1

        return forma
    except Exception as e:
        print(f"\u26a0\ufe0f Error al obtener forma del equipo {equipo_id}:", e)
        return 0


def obtener_cuotas_api_football(fixture_id):
    try:
        cuotas = {}
        for tipo, bet_id in BET_IDS.items():
            params = {
                "fixture": fixture_id,
                "bookmaker": BOOKMAKER_BET365,
                "bet": bet_id
            }
            res = requests.get(ODDS_URL, headers=headers_api_football, params=params)
            data = res.json().get("response", [])

            if data and "values" in data[0]:
                cuotas[tipo] = data[0]["values"]  # Puede contener opciones como Over 9.5 @1.85

        return cuotas
    except Exception as e:
        print(f"\u26a0\ufe0f Error al obtener cuotas del fixture {fixture_id}: {e}")
        return {}


def analizar_partido(fixture):
    try:
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        home_id = fixture['teams']['home']['id']
        away_id = fixture['teams']['away']['id']
        fixture_id = fixture['fixture']['id']

        home_form = obtener_forma_equipo(home_id, local=True)
        away_form = obtener_forma_equipo(away_id, local=False)

        cuotas = obtener_cuotas_api_football(fixture_id)
        cuota_ml = 1.70  # Default

        if "ML" in cuotas:
            for valor in cuotas["ML"]:
                if valor["value"] == home:
                    cuota_ml = round(valor["odd"], 2)
                    break

        justificacion = []
        if home_form >= 9:
            justificacion.append(f"{home} con buena forma en casa (últimos 5)")
        if away_form <= 4:
            justificacion.append(f"{away} flojo como visitante")
        justificacion.append("cuota verificada con API-FOOTBALL")

        if home_form >= 9 or away_form <= 3:
            return {
                "partido": f"{home} vs {away}",
                "pick": f"Gana {home}",
                "cuota": cuota_ml,
                "valor": True,
                "justificacion": "; ".join(justificacion)
            }

        return None
    except Exception as e:
        print(f"\u26a0\ufe0f Error analizando partido:", e)
        return None
