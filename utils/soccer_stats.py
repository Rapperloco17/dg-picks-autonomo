import requests
from utils.api_football import HEADERS, BASE_URL

def obtener_estadisticas_fixture(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics"
    params = {
        "fixture": fixture_id
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if data.get("errors"):
            print(f"API error: {data['errors']}")
            return None

        estadisticas = {
            "local": {},
            "visitante": {}
        }

        for equipo in data.get("response", []):
            team_name = equipo.get("team", {}).get("name", "")
            stats = equipo.get("statistics", [])

            for stat in stats:
                tipo = stat.get("type")
                valor = stat.get("value")
                if equipo.get("team", {}).get("name") == team_name:
                    if equipo.get("team", {}).get("id") == data["response"][0]["team"]["id"]:
                        estadisticas["local"][tipo] = valor
                    else:
                        estadisticas["visitante"][tipo] = valor

        return estadisticas

    except Exception as e:
        print(f"Error al obtener estadísticas del fixture: {str(e)}")
        return None

