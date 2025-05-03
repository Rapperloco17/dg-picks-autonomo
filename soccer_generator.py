import json
from utils.api_football import obtener_partidos_de_liga, get_team_statistics, get_predictions
from analysis.match_insights import analizar_partido_profundo


def generar_picks_soccer():
    with open("utils/leagues_whitelist_ids.json") as f:
        ligas_validas = json.load(f)

    resultados = []

    for liga_id in ligas_validas:
        fixtures = obtener_partidos_de_liga(liga_id, None).get("response", [])

        for fixture in fixtures:
            fixture_id = fixture.get("fixture", {}).get("id")
            if not fixture_id:
                continue

            stats = get_team_statistics(fixture_id)
            prediction = get_predictions(fixture_id)

            if not stats or not prediction:
                print(f"⚠️ No se pudieron obtener datos para fixture {fixture_id}")
                continue

            pick_data = analizar_partido_profundo(fixture, stats, prediction)

            if pick_data:
                resultados.append(pick_data)

    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    generar_picks_soccer()
