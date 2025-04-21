# utils/soccer_stats.py – Conexión total: corners, tarjetas, faltas, análisis completo

import requests
from utils.telegram import enviar_mensaje
from utils.corners_stats import analizar_corners_avanzado
from utils.corners_equipo import analizar_corners_por_equipo
from utils.cards_stats import analizar_tarjetas
from utils.fouls_stats import analizar_faltas

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
ODDS_URL = "https://v3.football.api-sports.io/odds"

BOOKMAKER_BET365 = 6
BET_IDS = {
    "ML": 1,
    "DOUBLE_CHANCE": 12,
    "OVER_UNDER": 5,
    "CORNERS": 121
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
                    if v["value"] in ["Over 1.5", "Over 2.5", "Over 3.5", "Under 2.5"]:
                        cuotas[v["value"]] = round(float(v["odd"]), 2)
            elif tipo == "CORNERS":
                for v in valores:
                    if "Over 9.5" in v["value"] or "Under 9.5" in v["value"]:
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

        # Conexiones automáticas a módulos físicos
        analizar_corners_avanzado(fixture)
        analizar_corners_por_equipo(fixture)
        analizar_tarjetas(fixture)
        analizar_faltas(fixture)

        home_form = obtener_forma_equipo(home_id, local=True)
        away_form = obtener_forma_equipo(away_id, local=False)

        cuotas = obtener_cuotas_completas(fixture_id, home, away)
        if "ML" not in cuotas:
            return None

        cuota_final = cuotas["ML"]
        pick = f"Gana {home}"

        opciones = []
        if "1X" in cuotas:
            opciones.append((cuotas["1X"], f"{home} o Empate"))
        if "Over 1.5" in cuotas:
            opciones.append((cuotas["Over 1.5"], "Más de 1.5 goles"))
        if "Over 2.5" in cuotas:
            opciones.append((cuotas["Over 2.5"], "Más de 2.5 goles"))
        if "Over 3.5" in cuotas:
            opciones.append((cuotas["Over 3.5"], "Más de 3.5 goles"))
        if "Under 2.5" in cuotas:
            opciones.append((cuotas["Under 2.5"], "Menos de 2.5 goles"))
        if "Over 9.5" in cuotas:
            opciones.append((cuotas["Over 9.5"], "Más de 9.5 corners"))
        if "Under 9.5" in cuotas:
            opciones.append((cuotas["Under 9.5"], "Menos de 9.5 corners"))

        opciones.sort(reverse=True)
        for cuota, desc in opciones:
            if cuota > cuota_final and cuota >= 1.60:
                cuota_final = cuota
                pick = desc
                break

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
