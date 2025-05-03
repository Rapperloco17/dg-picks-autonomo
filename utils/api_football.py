import requests

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"  # TU API KEY ACTUAL
API_URL = "https://v3.football.api-sports.io/fixtures"

headers = {
    "x-apisports-key": API_KEY
}

def obtener_partidos_de_liga(liga_id, fecha, temporada):
    """
    Consulta la API para obtener los partidos de una liga específica en una fecha dada y temporada definida.
    :param liga_id: ID numérico de la liga (según API-FOOTBALL)
    :param fecha: Fecha en formato YYYY-MM-DD
    :param temporada: Año de la temporada (ej. 2024)
    :return: Lista de partidos del día para esa liga
    """
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha
    }

    response = requests.get(API_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", [])
    else:
        print(f"Error en la API: {response.status_code}")
        return []
