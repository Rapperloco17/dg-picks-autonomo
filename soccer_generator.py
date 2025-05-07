import json
import os
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.api_football import obtener_partidos_hoy
from utils.cuotas import obtener_cuota_fixture

RUTA_SALIDA = "output/picks_futbol.json"


def generar_picks():
    partidos = obtener_partidos_hoy()
    print(f"Se encontraron {len(partidos)} partidos para analizar.")

    picks_generados = []

    for partido in partidos:
        fixture_id = partido["fixture"]["id"]
        analisis = analizar_partido_futbol(partido)

        if analisis and "tipo" in analisis:
            tipo = analisis["tipo"]
            cuota = obtener_cuota_fixture(fixture_id, tipo)
            if cuota:
                analisis["cuota"] = cuota
                picks_generados.append(analisis)

    if picks_generados:
        os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
        with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
            json.dump(picks_generados, f, indent=4, ensure_ascii=False)

        print(f"✅ Picks generados y guardados en {RUTA_SALIDA}")
    else:
        print("⚠️ No se generaron picks para hoy.")


if __name__ == "__main__":
    generar_picks()


