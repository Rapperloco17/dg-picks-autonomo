# descargar_resultados_por_liga.py
import requests
import pandas as pd
import json
import time

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

LEAGUES = [
    (262, "Liga MX"), (140, "La Liga"), (39, "Premier League"), (135, "Serie A"), (78, "Bundesliga"),
    (61, "Ligue 1"), (88, "Eredivisie"), (94, "Primeira Liga"), (203, "Super Lig"), (144, "Jupiler Pro League"),
    (179, "Scottish Premiership"), (197, "Greek Super League"), (218, "Czech First League"),
    (222, "Swiss Super League"), (216, "Croatian HNL"), (195, "Austrian Bundesliga"),
    (219, "Hungarian NB I"), (197, "Danish Superliga"), (196, "Norwegian Eliteserien"),
    (239, "Swedish Allsvenskan"), (106, "Polish Ekstraklasa"), (224, "Romanian Liga I"),
    (218, "Bulgarian First League"), (245, "Finnish Veikkausliiga"), (207, "Slovak Superliga"),
    (2, "Champions League"), (3, "Europa League"), (848, "Conference League"),
    (13, "Copa Libertadores"), (11, "Copa Sudamericana"),
    (253, "MLS"), (71, "Brasileirao"), (128, "Liga Profesional Argentina"), (239, "Colombia Primera A"),
    (274, "Liga 1 Peru"), (275, "Primera Division Chile"), (289, "FUTVE Venezuela"), (290, "Primera Paraguay"),
    (291, "Primera Bolivia"), (292, "Primera Ecuador"), (293, "Primera Uruguay"),
    (40, "Championship"), (141, "Segunda Division España"), (201, "Serie B Brasil"),
    (129, "Primera Nacional Argentina"), (263, "Expansión MX")
]

TEMPORADA = 2024

for league_id, league_name in LEAGUES:
    print(f"Descargando {league_name}...")
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": TEMPORADA,
        "status": "FT"
    }

    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    partidos = []

    for item in data.get("response", []):
        if item['league']['id'] != league_id:
            continue  # filtrar por seguridad si se cuela otro

        fixture = item["fixture"]
        teams = item["teams"]
        goals = item["goals"]
        stats = {s['type']: (s['value'] if s['value'] is not None else 0)
                 for s in item.get("statistics", [{}])[0].get("statistics", [])}

        local = teams['home']['name']
        visitante = teams['away']['name']
        goles_local = goals['home']
        goles_visitante = goals['away']

        partido = {
            "fixture_id": fixture['id'],
            "fecha": fixture['date'][:10],
            "liga_id": league_id,
            "liga_nombre": league_name,
            "season": TEMPORADA,
            "round": fixture.get('round'),
            "local": local,
            "visitante": visitante,
            "goles_local": goles_local,
            "goles_visitante": goles_visitante,
            "posesion_local": stats.get("Ball Possession", 0),
            "tiros_local": stats.get("Total Shots", 0),
            "tiros_arco_local": stats.get("Shots on Goal", 0),
            "corners_local": stats.get("Corner Kicks", 0),
            "tarjetas_local": stats.get("Yellow Cards", 0),
            "resultado": (
                "local" if goles_local > goles_visitante else
                "visitante" if goles_visitante > goles_local else "empate"
            ),
            "ambos_anotan": goles_local > 0 and goles_visitante > 0,
            "over_2_5": (goles_local + goles_visitante) > 2.5,
            "fuentes": {
                "api": "API-FOOTBALL",
                "fecha_descarga": pd.Timestamp.now().strftime("%Y-%m-%d")
            }
        }

        partidos.append(partido)

    if partidos:
        json_filename = f"resultados_{league_name.replace(' ', '_').lower()}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(partidos, f, ensure_ascii=False, indent=2)

        df = pd.DataFrame(partidos)
        excel_filename = f"resultados_{league_name.replace(' ', '_').lower()}.xlsx"
        df.to_excel(excel_filename, index=False)

        print(f"✅ Guardado: {json_filename} y {excel_filename}")
    else:
        print(f"⚠️ No hay partidos finalizados para {league_name}")

    time.sleep(1.5)
