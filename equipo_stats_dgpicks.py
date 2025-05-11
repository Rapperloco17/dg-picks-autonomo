
import requests

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

def obtener_estadisticas_equipo(team_id, league_id, season=2024):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    data = response.json().get("response", {})

    estadisticas = {
        "forma": data.get("form"),
        "partidos_jugados": data.get("fixtures", {}).get("played", {}),
        "victorias": data.get("fixtures", {}).get("wins", {}),
        "derrotas": data.get("fixtures", {}).get("loses", {}),
        "empates": data.get("fixtures", {}).get("draws", {}),

        "goles": data.get("goals", {}),
        "promedio_goles": data.get("goals", {}).get("average", {}),

        "goles_1t": data.get("goals", {}).get("for", {}).get("minute", {}).get("0-15", {}),
        "clean_sheets": data.get("clean_sheet", {}),
        "sin_anotar": data.get("failed_to_score", {}),

        "penales": data.get("penalty", {}),
        "tiros": data.get("shots", {}),
        "posesion": data.get("lineups", {}),
        "promedio_posesion": data.get("biggest", {}).get("ball_possession", {}),

        "corners": data.get("lineups", {}),
        "tarjetas": data.get("cards", {}),
    }

    return estadisticas

def imprimir_estadisticas(equipo, stats):
    print(f"\n📊 Estadísticas de {equipo}")
    print(f"Forma reciente: {stats['forma']}")
    print(f"Goles promedio (local): {stats['promedio_goles'].get('home')} | (visita): {stats['promedio_goles'].get('away')}")
    print(f"Goles en 1T (0-15 min): {stats['goles_1t']}")
    print(f"Clean sheets: {stats['clean_sheets']}")
    print(f"Falla al anotar: {stats['sin_anotar']}")
    print(f"Tiros totales: {stats['tiros']}")
    print(f"Tarjetas: {stats['tarjetas']}")
    print(f"Promedio posesión: {stats['promedio_posesion']}")

def comparar_estadisticas_equipos(home_name, home_id, away_name, away_id, league_id, season=2024):
    stats_home = obtener_estadisticas_equipo(home_id, league_id, season)
    stats_away = obtener_estadisticas_equipo(away_id, league_id, season)

    if not stats_home or not stats_away:
        print("\n❌ No se pudieron obtener estadísticas de ambos equipos.")
        return

    print(f"\n🤜 Comparativa {home_name} vs {away_name}")
    print(f"Goles promedio: {home_name} local {stats_home['promedio_goles'].get('home')} | {away_name} visita {stats_away['promedio_goles'].get('away')}")
    print(f"Tiros al arco: {home_name} {stats_home['tiros']} | {away_name} {stats_away['tiros']}")
    print(f"Clean sheets: {home_name} {stats_home['clean_sheets']} | {away_name} {stats_away['clean_sheets']}")
    print(f"Fallas al anotar: {home_name} {stats_home['sin_anotar']} | {away_name} {stats_away['sin_anotar']}")
    print(f"Tarjetas: {home_name} {stats_home['tarjetas']} | {away_name} {stats_away['tarjetas']}")
    print(f"Posesión: {home_name} {stats_home['promedio_posesion']} | {away_name} {stats_away['promedio_posesion']}")
