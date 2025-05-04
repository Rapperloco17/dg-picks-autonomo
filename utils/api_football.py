import os
import requests

API_KEY = os.getenv("API_FOOTBALL_KEY")

def obtener_partidos_de_liga(liga_id, fecha, temporada):
    """
    Trae los partidos reales de una liga en una fecha específica usando API-FOOTBALL.

    :param liga_id: ID numérico de la liga
    :param fecha: string en formato 'YYYY-MM-DD'
    :param temporada: año de la temporada (ej. 2024)
    :return: lista de partidos con estructura estándar
    """
    print(f"Buscando partidos reales para liga {liga_id} - {fecha} - temporada {temporada}")

    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha,
        "timezone": "America/Mexico_City"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if data.get("errors"):
            print("❌ Error en respuesta de API:", data["errors"])
            return []

        partidos = data.get("response", [])
        print(f"✅ {len(partidos)} partidos encontrados")
        return partidos

    except Exception as e:
        print(f"❌ Error obteniendo partidos: {e}")
        return []
