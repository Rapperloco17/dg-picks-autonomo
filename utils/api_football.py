import requests

API_FOOTBALL_KEY = "178b66e41ba9d4d3b8549f096ef1e377"  # Tu API Key real
API_FOOTBALL_HOST = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}

def obtener_partidos_de_liga(liga_id, fecha, temporada):
    url = f"{API_FOOTBALL_HOST}/fixtures"
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if response.status_code != 200 or "response" not in data:
            print("⚠️ Error en respuesta de API-Football:", data)
            return []

        partidos = data["response"]
        partidos_filtrados = []

        for partido in partidos:
            partidos_filtrados.append({
                "fixture": partido["fixture"],
                "teams": partido["teams"],
                "league": partido["league"]
            })

        return partidos_filtrados

    except Exception as e:
        print(f"❌ Error al obtener partidos de liga {liga_id}: {str(e)}")
        return []

