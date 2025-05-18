
import requests
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

UMBRAL_GOLES = 65
UMBRAL_BTTS = 60
UMBRAL_CORNERS = 9
UMBRAL_TARJETAS = 4

LIGAS_VALIDAS_IDS = {
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73,
    45, 78, 79, 88, 94, 103, 106, 113, 119, 128, 129, 130,
    135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172,
    179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253,
    257, 262, 263, 265, 268, 271, 281, 345, 357
}

def obtener_fixtures_del_dia():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    partidos = []

    total = 0
    filtrados = 0

    for item in data.get("response", []):
        total += 1
        liga_id = item["league"]["id"]
        if liga_id not in LIGAS_VALIDAS_IDS:
            continue
        filtrados += 1
        partidos.append({
            "fixture_id": item["fixture"]["id"],
            "liga": item["league"]["name"],
            "liga_id": liga_id,
            "local": item["teams"]["home"]["name"],
            "visitante": item["teams"]["away"]["name"],
            "local_id": item["teams"]["home"]["id"],
            "visitante_id": item["teams"]["away"]["id"],
            "hora": item["fixture"]["date"]
        })

    print(f"\n📊 Total partidos recibidos: {total}")
    print(f"✅ Partidos en ligas válidas: {filtrados}")
    return partidos

def obtener_forma_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&season=2024&league={league_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    return response.json().get("response", {})

def obtener_predicciones(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
    data = response.json().get("response", [])
    if not data:
        return {}

    pred = data[0].get("predictions", {})
    goles = data[0].get("goals", {})

    return {
        "ganador": pred.get("winner", {}).get("name"),
        "btts_yes": pred.get("both_teams_to_score", {}).get("yes"),
        "btts_no": pred.get("both_teams_to_score", {}).get("no"),
        "over25": pred.get("goals", {}).get("over_2_5", {}).get("percentage"),
        "goles_home": goles.get("home"),
        "goles_away": goles.get("away")
    }

def obtener_h2h(local_id, visitante_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={local_id}-{visitante_id}&last=5"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    data = response.json().get("response", [])
    return [f"{p.get('goals', {}).get('home', 0)}-{p.get('goals', {}).get('away', 0)}" for p in data]


def obtener_cuotas(fixture_id):
    bookmaker_ids = [6, 1, 8, 9]  # Bet365, 1xBet, Pinnacle, William Hill
    for bookmaker_id in bookmaker_ids:
        url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker={bookmaker_id}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            continue
        data = response.json().get("response", [])
        cuotas = {}
        for mercado in data:
            for book in mercado.get("bookmakers", []):
                for tipo in book.get("bets", []):
                    if tipo["name"] == "Over/Under 2.5 goals":
                        for val in tipo.get("values", []):
                            if val["value"] == "Over 2.5":
                                cuotas["over_2_5"] = val["odd"]
                    if tipo["name"] == "Both Teams To Score":
                        for val in tipo.get("values", []):
                            if val["value"] == "Yes":
                                cuotas["btts"] = val["odd"]
                    if tipo["name"] == "Match Winner":
                        for val in tipo.get("values", []):
                            if val["value"] == "Home":
                                cuotas["local"] = val["odd"]
                            elif val["value"] == "Draw":
                                cuotas["empate"] = val["odd"]
                            elif val["value"] == "Away":
                                cuotas["visitante"] = val["odd"]
        if cuotas:
            return cuotas
    return {}



def analizar_historial_equipo(team_id, league_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&league={league_id}&season=2024&status=FT&limit=10"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"btts_pct": 0, "over25_pct": 0, "goles_prom": 0}

    data = response.json().get("response", [])
    if not data:
        return {"btts_pct": 0, "over25_pct": 0, "goles_prom": 0}

    btts_count = 0
    over25_count = 0
    total_goles = 0
    partidos_validos = 0

    for match in data:
        goals = match.get("goals", {})
        g1 = goals.get("home", 0)
        g2 = goals.get("away", 0)

        if g1 is not None and g2 is not None:
            partidos_validos += 1
            total_goles += g1 + g2
            if g1 > 0 and g2 > 0:
                btts_count += 1
            if g1 + g2 > 2.5:
                over25_count += 1

    if partidos_validos == 0:
        return {"btts_pct": 0, "over25_pct": 0, "goles_prom": 0}

    return {
        "btts_pct": round((btts_count / partidos_validos) * 100, 1),
        "over25_pct": round((over25_count / partidos_validos) * 100, 1),
        "goles_prom": round(total_goles / partidos_validos, 2)
    }



def obtener_historial_equipo(team_id, league_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&league={league_id}&season=2024&status=FT&limit=20"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None

    data = response.json().get("response", [])
    total = len(data)
    if total == 0:
        return None

    victorias = empates = derrotas = gf = gc = btts = over25 = 0

    for partido in data:
        goals = partido.get("goals", {})
        home = goals.get("home", 0)
        away = goals.get("away", 0)
        if partido["teams"]["home"]["id"] == team_id:
            goles_favor = home
            goles_contra = away
            if home > away:
                victorias += 1
            elif home == away:
                empates += 1
            else:
                derrotas += 1
        else:
            goles_favor = away
            goles_contra = home
            if away > home:
                victorias += 1
            elif home == away:
                empates += 1
            else:
                derrotas += 1

        gf += goles_favor
        gc += goles_contra

        if goles_favor > 0 and goles_contra > 0:
            btts += 1
        if goles_favor + goles_contra >= 3:
            over25 += 1

    return {
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "gf": gf,
        "gc": gc,
        "prom_goles": round((gf + gc) / total, 2),
        "btts_pct": round((btts / total) * 100, 1),
        "over25_pct": round((over25 / total) * 100, 1)
    }
