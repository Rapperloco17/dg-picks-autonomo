import os
import json
from datetime import datetime, timedelta
from utils.api_football import get_fixtures_today

# Archivos de ligas y temporadas
with open("utils/leagues_whitelist_ids.json", "r", encoding="utf-8") as f:
    leagues_whitelist = json.load(f)

with open("utils/league_seasons.json", "r", encoding="utf-8") as f:
    league_seasons = json.load(f)

# Obtener fixtures del día siguiente
def get_fixtures():
    fixtures = []
    # Cambia esta línea para pedir mañana:
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y-%m-%d")

    for league_id in leagues_whitelist:
        season = league_seasons.get(str(league_id), 2024)

        url = f"https://v3.football.api-sports.io/fixtures?date={date_str}&league={league_id}&season={season}"
        headers = {
            "x-apisports-key": "178b66e41ba9d4d3b8549f096ef1e377"
        }

        try:
            response = get_fixtures_today(url, headers)
            if response:
                fixtures.extend(response)
            else:
                print(f"⚠️  No hay partidos en liga {league_id} temporada {season}")
        except Exception as e:
            print(f"❌ Error al consultar liga {league_id}: {e}")

    return fixtures

# Guardar archivo
def main():
    fixtures = get_fixtures()
    print(f"📊 Total de partidos encontrados: {len(fixtures)}")

    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = f"outputs/futbol_{hoy}.json"

    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump({"picks": fixtures}, f, indent=2, ensure_ascii=False)

    print(f"✅ Partidos guardados en {archivo_salida}")

if __name__ == "__main__":
    main()
