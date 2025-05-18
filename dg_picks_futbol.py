import os
import requests
from datetime import date

# Cargar la API Key desde las variables de entorno
API_KEY = os.getenv("API_FOOTBALL_KEY")

# Headers para la API
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

# IDs de ligas válidas
ligas_validas = {
    2, 3, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94, 103,
    106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164,
    169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262,
    263, 265, 268, 271, 281, 345, 357
}

# Obtener partidos del día
fecha_hoy = date.today().strftime("%Y-%m-%d")
url = f"https://v3.football.api-sports.io/fixtures?date={fecha_hoy}"
response = requests.get(url, headers=headers)
data = response.json()

print("\U0001F4C5 Análisis de partidos del día", fecha_hoy)
partidos = data.get("response", [])
print("\u2728 Total partidos encontrados:", len(partidos))

for f in partidos:
    fixture = f.get("fixture", {})
    league = f.get("league", {})
    teams = f.get("teams", {})
    goals = f.get("goals", {})
    stats = f.get("statistics", [])

    liga_id = league.get("id")
    if liga_id not in ligas_validas:
        continue

    nombre_partido = f"{teams['home']['name']} vs {teams['away']['name']} ({league['name']})"
    print("\n\U0001F3C6", nombre_partido)

    # Obtener estadísticas para marcador tentativo
    id_fixture = fixture.get("id")
    url_stats = f"https://v3.football.api-sports.io/teams/statistics?season=2024&team={teams['home']['id']}&league={liga_id}"
    stats_local = requests.get(url_stats, headers=headers).json()
    url_stats = f"https://v3.football.api-sports.io/teams/statistics?season=2024&team={teams['away']['id']}&league={liga_id}"
    stats_visitante = requests.get(url_stats, headers=headers).json()

    try:
        gf_local = float(stats_local['response']['goals']['for']['average']['home'] or 0)
        gc_local = float(stats_local['response']['goals']['against']['average']['home'] or 0)
        gf_visitante = float(stats_visitante['response']['goals']['for']['average']['away'] or 0)
        gc_visitante = float(stats_visitante['response']['goals']['against']['average']['away'] or 0)

        marcador_local = round((gf_local + gc_visitante) / 2)
        marcador_visitante = round((gf_visitante + gc_local) / 2)

        print(f"\U0001F4CA Marcador tentativo: {marcador_local} - {marcador_visitante}")
    except Exception as e:
        print("\u26A0\ufe0f Error al calcular marcador tentativo:", e)
        continue
