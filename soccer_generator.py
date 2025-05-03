import json
from utils.api_football import obtener_partidos_de_liga, get_team_statistics, get_predictions
from analysis.match_insights import analizar_partido_profundo


def generar_picks_soccer():
    print("\ud83d\udd26 Iniciando an\u00e1lisis DG Picks...")
    with open("utils/leagues_whitelist.json") as f:
        ligas = json.load(f)

    resultados = []

    for liga in ligas:
        partidos = obtener_partidos_de_liga(liga, None)
        fixtures = partidos.get("response", [])

        for fixture in fixtures:
            fixture_id = fixture.get("fixture", {}).get("id")
            if not fixture_id:
                continue

            stats = get_team_statistics(fixture_id)
            prediction = get_predictions(fixture_id)

            if stats and prediction:
                try:
                    pick_info = analizar_partido_profundo(fixture, stats, prediction)
                    if pick_info:
                        resultados.append(pick_info)
                except Exception as e:
                    print(f"\u274c Error en an\u00e1lisis profundo del fixture {fixture_id}: {e}")
            else:
                print(f"\u26a0\ufe0f No se pudieron obtener datos para fixture {fixture_id}")

    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    generar_picks_soccer()

if __name__ == "__main__":
    generar_picks_soccer()
