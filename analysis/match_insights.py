import requests
from datetime import datetime

# Header con tu API Key de API-FOOTBALL
API_FOOTBALL_HEADERS = {
    "x-apisports-key": "178b66e41ba9d4d3b8549f096ef1e377"
}

def analizar_partido_profundo(fixture, stats, prediction):
    razonamiento = []
    pick = None

    fixture_id = fixture["fixture"]["id"]
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    league = fixture["league"]["name"]
    date = fixture["fixture"]["date"]

    home_stats = stats.get("home", {}).get("teams", {}).get("statistics", {})
    away_stats = stats.get("away", {}).get("teams", {}).get("statistics", {})

    advice = prediction.get("advice", "")

    # Goles promedio, tiros, forma
    home_goals = home_stats.get("Goals scored", 0)
    away_goals = away_stats.get("Goals scored", 0)
    home_concede = home_stats.get("Goals conceded", 0)
    away_concede = away_stats.get("Goals conceded", 0)

    if home_goals and away_goals and home_concede and away_concede:
        if home_goals + away_goals >= 3 and home_concede + away_concede >= 2:
            razonamiento.append(
                f"Ambos equipos tienen buena producción ofensiva y defensiva débil: {home} ({home_goals} GF / {home_concede} GA), {away} ({away_goals} GF / {away_concede} GA)"
            )
            pick = "Over 2.5 goles"

        elif home_concede + away_concede >= 3:
            razonamiento.append(
                f"Ambos equipos permiten muchos goles: {home} concede {home_concede}, {away} concede {away_concede}"
            )
            pick = "Ambos anotan (BTTS)"

        elif home_goals >= 1.5 and away_concede >= 1.5:
            razonamiento.append(
                f"{home} promedia {home_goals} goles a favor y {away} concede {away_concede} por partido."
            )
            pick = f"{home} gana"

    # Validación con predicción del API
    if pick and advice and pick.lower() in advice.lower():
        razonamiento.append(f"✅ El consejo del API también sugiere: '{advice}'")
    elif pick:
        razonamiento.append(f"⚠️ El pick se genera por análisis real, aunque el API no lo recomienda directamente.")

    if not pick:
        return None  # No se detectó valor real

    return {
        "fixture_id": fixture_id,
        "match": f"{home} vs {away}",
        "league": league,
        "fecha": date,
        "pick": pick,
        "razonamiento": razonamiento
    }
