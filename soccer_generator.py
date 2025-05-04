import json
from api_football import obtener_estadisticas_y_cuotas
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.partidos_disponibles import obtener_partidos_disponibles

def generar_picks_soccer():
    partidos = obtener_partidos_disponibles()
    picks_detectados = []

    for partido in partidos:
        fixture_id = partido.get("fixture", {}).get("id")
        if not fixture_id:
            continue

        datos_estadisticos, cuotas = obtener_estadisticas_y_cuotas(fixture_id)
        if not datos_estadisticos or not cuotas:
            continue

        resultado = analizar_partido_futbol(partido, datos_estadisticos, cuotas)

        if resultado["valor"]:
            picks_detectados.append({
                "fixture_id": fixture_id,
                "partido": f"{partido['teams']['home']['name']} vs {partido['teams']['away']['name']}",
                "pick": resultado["pick"],
                "motivo": resultado["motivo"],
                "cuota": resultado["cuota"]
            })

    with open("picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(picks_detectados, f, indent=4, ensure_ascii=False)

    print(f"✅ Picks generados: {len(picks_detectados)}")
    return picks_detectados

if __name__ == "__main__":
    generar_picks_soccer()
