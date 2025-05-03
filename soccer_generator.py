import json
from utils.api_football import obtener_partidos_de_liga, get_team_statistics, get_predictions
from analysis.match_insights import analizar_partido_profundo

# Cargar ligas permitidas desde JSON
with open("utils/leagues_whitelist.json", "r", encoding="utf-8") as f:
    ligas_ids = json.load(f)

def generar_picks_soccer():
    print("Iniciando análisis DG Picks...")

    resultados = []

    for liga_id in ligas_ids:
        fixtures_response = obtener_partidos_de_liga(liga_id, fecha=None)
        fixtures = fixtures_response.get("response", [])

        for fixture in fixtures:
            fixture_id = fixture.get("fixture", {}).get("id")
            if not fixture_id:
                continue

            stats = get_team_statistics(fixture_id)
            prediction = get_predictions(fixture_id)

            if stats and prediction:
                pick_info = analizar_partido_profundo(fixture, stats, prediction)
                if pick_info:
                    resultados.append(pick_info)

    # Guardar resultados
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

    print("✅ Picks de fútbol generados y guardados correctamente.")

if __name__ == "__main__":
    generar_picks_soccer()

