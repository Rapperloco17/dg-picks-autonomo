import os
import json
from datetime import datetime
from utils.api_football import get_fixtures_today

# Cargar API key
API_KEY = os.getenv("API_FOOTBALL_KEY") or "178b66e41ba9d4d3b8549f096ef1e377"

# Cargar whitelist de ligas
with open("utils/leagues_whitelist_ids.json", "r", encoding="utf-8") as f:
    leagues_whitelist = json.load(f)["allowed_league_ids"]

# Cargar temporadas por liga
with open("utils/league_seasons.json", "r", encoding="utf-8") as f:
    league_seasons = json.load(f)

# Obtener fixtures del día
def get_fixtures():
    fixtures = []
    today = datetime.now().strftime("%Y-%m-%d")

    for league_id in leagues_whitelist:
        season = league_seasons.get(str(league_id), 2024)

        url = f"https://v3.football.api-sports.io/fixtures?date={today}&league={league_id}&season={season}"
        headers = {"x-apisports-key": API_KEY}

        try:
            response = get_fixtures_today(url, headers)
            if response:
                fixtures.extend(response)
            else:
                print(f"⚠️ No hay partidos en liga {league_id} temporada {season}")
        except Exception as e:
            print(f"❌ Error al consultar liga {league_id}: {e}")

    return fixtures

# Guardar archivo
if __name__ == "__main__":
    fixtures = get_fixtures()
    print(f"📋 Total de partidos encontrados: {len(fixtures)}")

    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = f"outputs/futbol_{hoy}.json"

    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump({"picks": fixtures}, f, indent=2, ensure_ascii=False)

    print(f"✅ Partidos guardados en {archivo_salida}")
