# utils/soccer_stats.py – Cuotas reales (ML, Doble Oportunidad, Over/Under) 100% activas

import requests

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
ODDS_URL = "https://v3.football.api-sports.io/odds"

BOOKMAKER_BET365 = 6
BET_IDS = {
    "ML": 1,
    "DOUBLE_CHANCE": 12,
    "OVER_UNDER": 5
}


def obtener_forma_equipo(equipo_id, local=True):
    try:
        params = {"team": equipo_id, "last": 5}
        if local:
            params["venue"] = "home"
        else:
            params["venue"] = "away"

        res = requests.get(FIXTURES_URL, headers=HEADERS, params=params)
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
        print(f"\u26a0\ufe0f Error forma equipo {equipo_id}: {e}")
        return 0


def obtener_cuotas_completas(fixture_id, home_name, away_name):
    cuotas = {}
    try:
        for tipo, bet_id in BET_IDS.items():
            params = {
                "fixture": fixture_id,
                "bookmaker": BOOKMAKER_BET365,
                "bet": bet_id
            }
            res = requests.get(ODDS_URL, headers=HEADERS, params=params)
            data = res.json().get("response", [])

            if not data:
                continue

            valores = data[0].get("values", [])
            if tipo == "ML":
                for v in valores:
                    if v["value"] == home_name:
                        cuotas["ML"] = round(float(v["odd"]), 2)
            elif tipo == "DOUBLE_CHANCE":
                for v in valores:
                    cuotas[v["value"]] = round(float(v["odd"]), 2)
            elif tipo == "OVER_UNDER":
                for v in valores:
                    if "Over" in v["value"] or "Under" in v["value"]:
                        cuotas[v["value"]] = round(float(v["odd"]), 2)
    except Exception as e:
        print(f"\u26a0\ufe0f Error obteniendo cuotas fixture {fixture_id}: {e}")

    return cuotas


def analizar_partido(fixture):
    try:
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        home_id = fixture['teams']['home']['id']
        away_id = fixture['teams']['away']['id']
        fixture_id = fixture['fixture']['id']

        home_form = obtener_forma_equipo(home_id, local=True)
        away_form = obtener_forma_equipo(away_id, local=False)

        cuotas = obtener_cuotas_completas(fixture_id, home, away)
        if "ML" not in cuotas:
            return None

        cuota_final = cuotas["ML"]
        pick = f"Gana {home}"

        # Si ML es muy baja pero 1X o Over 2.5 tienen más valor, podemos usar otra apuesta
        if cuota_final < 1.50:
            if "1X" in cuotas and cuotas["1X"] >= 1.60:
                pick = f"{home} o Empate"
                cuota_final = cuotas["1X"]
            elif "Over 2.5" in cuotas and cuotas["Over 2.5"] >= 1.65:
                pick = "Más de 2.5 goles"
                cuota_final = cuotas["Over 2.5"]

        justificacion = []
        if home_form >= 9:
            justificacion.append(f"{home} en buena forma en casa")
        if away_form <= 4:
            justificacion.append(f"{away} flojo como visitante")
        justificacion.append("cuota validada con API-FOOTBALL")

        return {
            "partido": f"{home} vs {away}",
            "pick": pick,
            "cuota": cuota_final,
            "valor": True,
            "justificacion": "; ".join(justificacion),
            "cuotas": cuotas
        }

    except Exception as e:
        print(f"\u26a0\ufe0f Error analizando partido:", e)
        return None
