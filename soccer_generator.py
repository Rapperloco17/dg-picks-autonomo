import os
import json
from utils.api_football import obtener_partidos_de_liga, get_team_statistics, get_predictions
from analysis.match_insights import analizar_partido_profundo

def generar_picks_soccer():
    print("Iniciando analisis DG Picks...")

    from utils.leagues_whitelist_ids import ligas_ids
    output_folder = "output"
    output_file = os.path.join(output_folder, "picks_futbol.json")

    # Crear carpeta si no existe
    os.makedirs(output_folder, exist_ok=True)

    picks = []

    for liga_id in ligas_ids:
        response = obtener_partidos_de_liga(liga_id, None)
        fixtures = response.get("response", [])

        for fixture in fixtures:
            fixture_id = fixture.get("fixture", {}).get("id")
            if not fixture_id:
                continue

            stats = get_team_statistics(fixture_id)
            prediction = get_predictions(fixture_id)

            if not stats or not prediction:
                continue

            pick = analizar_partido_profundo(fixture, stats, prediction)
            if pick:
                picks.append(pick)

    # Guardar resultados
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)

    print(f"Picks de fútbol generados: {len(picks)}")

if __name__ == "__main__":
    generar_picks_soccer()

