
import requests

API_FOOTBALL_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
API_FOOTBALL_HOST = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_FOOTBALL_KEY
}

def obtener_fixtures(fecha):
    url = f"{API_FOOTBALL_HOST}/fixtures?date={fecha}&timezone=America/Mexico_City"
    response = requests.get(url, headers=headers)
    return response.json()

def obtener_estadisticas_partido(fixture_id):
    url = f"{API_FOOTBALL_HOST}/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    return response.json()

def obtener_partidos_de_liga(league_id, season):
    url = f"{API_FOOTBALL_HOST}/fixtures?league={league_id}&season={season}&timezone=America/Mexico_City"
    response = requests.get(url, headers=headers)
    return response.json()

def obtener_detalles_fixture(fixture_id):
    url = f"{API_FOOTBALL_HOST}/fixtures?id={fixture_id}&timezone=America/Mexico_City"
    response = requests.get(url, headers=headers)
    return response.json()
