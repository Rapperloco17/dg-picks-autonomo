import json
import os
from utils.api_football import obtener_partidos_de_liga, get_team_statistics, get_predictions

def generar_picks_soccer():
    print("⚽ Iniciando análisis DG Picks...")

    with open("utils/leagues_whitelist_ids.json", "r", encoding="utf-8") as f:
        ligas_ids = json.load(f)

    from datetime import datetime
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    all_picks = []

    for liga_id in ligas_ids:
        partidos = obtener_partidos_de_liga(liga_id, fecha_hoy)

        for fixture in partidos.get("response", []):
            stats = get_team_statistics(fixture["fixture"]["id"])
            if not stats:
                continue

            pred = get_predictions(fixture["fixture"]["id"])
            if not pred:
                continue

            # Ejemplo básico de criterio: más de 2.5 goles si ambos equipos promedian más de 1.5 goles a favor
            try:
                goles_local = stats["teams"]["home"]["statistics"]["goals"]["for"]["average"]["total"]
                goles_visitante = stats["teams"]["away"]["statistics"]["goals"]["for"]["average"]["total"]
                if goles_local and goles_visitante:
                    goles_local = float(goles_local)
                    goles_visitante = float(goles_visitante)
                    if goles_local > 1.4 and goles_visitante > 1.4:
                        pick = {
                            "partido": f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}",
                            "mercado": "Más de 2.5 goles",
                            "fecha": fixture["fixture"]["date"]
                        }
                        all_picks.append(pick)
            except:
                continue

    os.makedirs("output", exist_ok=True)
    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(all_picks, f, indent=4, ensure_ascii=False)

    print("✅ Picks generados correctamente.")
