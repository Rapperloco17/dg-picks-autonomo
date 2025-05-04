import requests

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def obtener_estadisticas_y_cuotas(fixture_id):
    try:
        url_stats = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
        url_form = f"{BASE_URL}/teams/statistics?fixture={fixture_id}"
        url_odds = f"{BASE_URL}/odds?fixture={fixture_id}"

        stats_response = requests.get(url_stats, headers=HEADERS).json()
        odds_response = requests.get(url_odds, headers=HEADERS).json()

        datos_estadisticos = {
            "local": {
                "goles_promedio": 0,
                "btts": 0,
                "forma": [],
                "invicto_local": False
            },
            "visitante": {
                "goles_promedio": 0,
                "btts": 0,
                "forma": [],
                "invicto_visitante": False
            }
        }

        if stats_response.get("response"):
            for team_stats in stats_response["response"]:
                equipo = "local" if team_stats["team"]["id"] == team_stats["team"]["id"] else "visitante"
                stats = team_stats.get("statistics", [])

                for stat in stats:
                    tipo = stat.get("type")
                    valor = stat.get("value")

                    if tipo == "Goals per match" and isinstance(valor, (int, float)):
                        datos_estadisticos[equipo]["goles_promedio"] = valor
                    elif tipo == "Both teams scored" and isinstance(valor, (int, float)):
                        datos_estadisticos[equipo]["btts"] = valor / 100

        # Suplencia con forma (dummy ajustable a datos reales si se activa otra petición)
        datos_estadisticos["local"]["forma"] = ["W", "W", "D", "L", "W"]
        datos_estadisticos["visitante"]["forma"] = ["L", "L", "D", "W", "L"]
        datos_estadisticos["local"]["invicto_local"] = True
        datos_estadisticos["visitante"]["invicto_visitante"] = False

        cuotas = {
            "over_1.5": 0,
            "over_2.5": 0,
            "over_3.5": 0,
            "under_1.5": 0,
            "under_2.5": 0,
            "under_3.5": 0,
            "btts": 0,
            "1X": 0,
            "X2": 0,
            "12": 0,
            "ml_local": 0,
            "ml_visitante": 0,
            "empate": 0,
            "draw_no_bet_home": 0
        }

        if odds_response.get("response"):
            for bookie in odds_response["response"]:
                for bet in bookie.get("bookmakers", []):
                    for market in bet.get("bets", []):
                        if market.get("name") == "Match Winner":
                            for val in market.get("values", []):
                                if val["value"] == "Home":
                                    cuotas["ml_local"] = float(val["odd"])
                                elif val["value"] == "Away":
                                    cuotas["ml_visitante"] = float(val["odd"])
                                elif val["value"] == "Draw":
                                    cuotas["empate"] = float(val["odd"])

                        elif market.get("name") == "Over/Under":
                            for val in market.get("values", []):
                                if "Over 1.5" in val["value"]:
                                    cuotas["over_1.5"] = float(val["odd"])
                                elif "Over 2.5" in val["value"]:
                                    cuotas["over_2.5"] = float(val["odd"])
                                elif "Over 3.5" in val["value"]:
                                    cuotas["over_3.5"] = float(val["odd"])
                                elif "Under 1.5" in val["value"]:
                                    cuotas["under_1.5"] = float(val["odd"])
                                elif "Under 2.5" in val["value"]:
                                    cuotas["under_2.5"] = float(val["odd"])
                                elif "Under 3.5" in val["value"]:
                                    cuotas["under_3.5"] = float(val["odd"])

                        elif market.get("name") == "Both Teams To Score":
                            for val in market.get("values", []):
                                if val["value"] == "Yes":
                                    cuotas["btts"] = float(val["odd"])

                        elif market.get("name") == "Double Chance":
                            for val in market.get("values", []):
                                if val["value"] == "1X":
                                    cuotas["1X"] = float(val["odd"])
                                elif val["value"] == "X2":
                                    cuotas["X2"] = float(val["odd"])
                                elif val["value"] == "12":
                                    cuotas["12"] = float(val["odd"])

                        elif market.get("name") == "Draw No Bet":
                            for val in market.get("values", []):
                                if val["value"] == "Home":
                                    cuotas["draw_no_bet_home"] = float(val["odd"])

        return datos_estadisticos, cuotas

    except Exception as e:
        print(f"Error en obtener_estadisticas_y_cuotas: {e}")
        return {}, {}
