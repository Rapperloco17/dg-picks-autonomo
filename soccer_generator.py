import json
from datetime import datetime
from utils.api_football import obtener_partidos_de_liga, get_team_statistics, get_predictions
from analysis.match_insights import analizar_partido_profundo
import os

def generar_picks_soccer():
    print("⚙️ Iniciando análisis DG Picks...")

    with open("utils/leagues_whitelist_ids.json") as f:
        ligas = json.load(f)

    resultados = []
    hoy = datetime.now().strftime("%Y-%m-%d")

    for liga_id in ligas:
        partidos = obtener_partidos_de_liga(liga_id, hoy)

        for fixture in partidos:
            stats = get_team_statistics(fixture["fixture"]["id"])
            prediction = get_predictions(fixture["fixture"]["id"])

            if stats and prediction:
                try:
                    pick = analizar_partido_profundo(fixture, stats, prediction)
                    if pick:
                        resultados.append(pick)
                except Exception as e:
                    print(f"❌ Error en análisis profundo del fixture {fixture['fixture']['id']}: {e}")
            else:
                print(f"⚠️ No se pudieron obtener datos para fixture {fixture['fixture']['id']}")

    # Guardar resultados
    os.makedirs("historial/fixtures", exist_ok=True)
    fecha_archivo = datetime.now().strftime("%Y-%m-%d")
    path_archivo = f"historial/fixtures/{fecha_archivo}.json"

    with open(path_archivo, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"✅ Análisis del día guardado en: {path_archivo}")
    print(f"📊 Proceso finalizado: {len(resultados)} partidos analizados | {len([r for r in resultados if r])} picks generados.")


if __name__ == "__main__":
    generar_picks_soccer()
