import requests
import datetime
import json

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}

def obtener_partidos_disponibles():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 Iniciando búsqueda de partidos para el {hoy}")

    try:
        with open("utils/leagues_whitelist.json", "r", encoding="utf-8") as f:
            ligas_permitidas = json.load(f)
    except Exception as e:
        print(f"❌ Error al leer leagues_whitelist.json: {e}")
        return []

    try:
        with open("utils/league_seasons.json", "r", encoding="utf-8") as f:
            temporadas = json.load(f)
    except Exception as e:
        print(f"❌ Error al leer league_seasons.json: {e}")
        return []

    partidos_filtrados = []

    for liga in ligas_permitidas:
        season = temporadas.get(str(liga))
        if not season:
            print(f"⚠️ No hay temporada registrada para la liga {liga}")
            continue

        url = f"https://v3.football.api-sports.io/fixtures"
        params = {
            "league": liga,
            "season": season,
            "date": hoy
        }

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"❌ Error al consultar la API para liga {liga}: {response.status_code}")
            continue

        data = response.json()
        fixtures = data.get("response", [])
        print(f"📦 Liga {liga} – Partidos recibidos: {len(fixtures)}")

        for partido in fixtures:
            status = partido.get("fixture", {}).get("status", {}).get("short")
            if status in ["NS", "TBD"]:
                partidos_filtrados.append(partido)

    print(f"✅ Total de partidos válidos encontrados: {len(partidos_filtrados)}")
    return partidos_filtrados
