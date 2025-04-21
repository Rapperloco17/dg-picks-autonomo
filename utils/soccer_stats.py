# utils/soccer_stats.py – ahora con análisis de Ambos Anotan (BTTS)

import requests
from utils.telegram import enviar_mensaje
from utils.corners_stats import analizar_corners_avanzado
from utils.corners_equipo import analizar_corners_por_equipo
from utils.cards_stats import analizar_tarjetas
from utils.fouls_stats import analizar_faltas
from utils.cache import cargar_fixture_cache, guardar_fixture_cache, fixture_en_cache
from utils.historial_picks import guardar_pick_en_historial

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
ODDS_URL = "https://v3.football.api-sports.io/odds"

BOOKMAKER_BET365 = 6
BET_IDS = {
    "ML": 1,
    "DOUBLE_CHANCE": 12,
    "OVER_UNDER": 5,
    "CORNERS": 121,
    "BTTS": both_teams_to_score := 13
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


def obtener_fixture_completo(fixture_id):
    if fixture_en_cache(fixture_id):
        return cargar_fixture_cache(fixture_id)
    else:
        url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}&timezone=America/Mexico_City"
        res = requests.get(url, headers=HEADERS)
        data = res.json().get("response", [])
        if data:
            guardar_fixture_cache(fixture_id, data[0])
            return data[0]
        return None


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
                    if v["value"] in ["Over 1.5", "Over 2.5", "Over 3.5", "Under 2.5", "Under 3.5"]:
                        cuotas[v["value"]] = round(float(v["odd"]), 2)
            elif tipo == "CORNERS":
                for v in valores:
                    if "Over 9.5" in v["value"] or "Under 9.5" in v["value"]:
                        cuotas[v["value"]] = round(float(v["odd"]), 2)
            elif tipo == "BTTS":
                for v in valores:
                    if v["value"] in ["Yes", "No"]:
                        cuotas[f"BTTS_{v['value']}"] = round(float(v["odd"]), 2)
    except Exception as e:
        print(f"\u26a0\ufe0f Error obteniendo cuotas fixture {fixture_id}: {e}")

    return cuotas


def analizar_partido(fixture):
    try:
        fixture_id = fixture['fixture']['id']
        full_fixture = obtener_fixture_completo(fixture_id)
        if not full_fixture:
            print(f"\u274c No se encontró fixture completo para ID {fixture_id}")
            return None

        home = full_fixture['teams']['home']['name']
        away = full_fixture['teams']['away']['name']
        home_id = full_fixture['teams']['home']['id']
        away_id = full_fixture['teams']['away']['id']

        print(f"\n\ud83d\udd39 Analizando: {home} vs {away}")

        analizar_corners_avanzado(full_fixture)
        analizar_corners_por_equipo(full_fixture)
        analizar_tarjetas(full_fixture)
        analizar_faltas(full_fixture)

        home_form = obtener_forma_equipo(home_id, local=True)
        away_form = obtener_forma_equipo(away_id, local=False)

        cuotas = obtener_cuotas_completas(fixture_id, home, away)
        if "ML" not in cuotas:
            print("\u274c No hay cuota ML disponible, se descarta")
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
        if "Under 3.5" in cuotas:
            opciones.append((cuotas["Under 3.5"], "Menos de 3.5 goles"))
        if "Over 9.5" in cuotas:
            opciones.append((cuotas["Over 9.5"], "Más de 9.5 corners"))
        if "Under 9.5" in cuotas:
            opciones.append((cuotas["Under 9.5"], "Menos de 9.5 corners"))

        # Ambos Anotan (BTTS)
        if "BTTS_Yes" in cuotas:
            opciones.append((cuotas["BTTS_Yes"], "Ambos equipos anotan"))
        if "BTTS_No" in cuotas:
            opciones.append((cuotas["BTTS_No"], "No anotan ambos equipos"))

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

        resultado = {
            "partido": f"{home} vs {away}",
            "pick": pick,
            "cuota": cuota_final,
            "valor": True,
            "justificacion": "; ".join(justificacion),
            "cuotas": cuotas
        }

        print(f"\u2705 PICK: {pick} | Cuota: {cuota_final}")

        guardar_pick_en_historial(resultado)
        return resultado

    except Exception as e:
        print(f"\u26a0\ufe0f Error analizando partido:", e)
        return None
