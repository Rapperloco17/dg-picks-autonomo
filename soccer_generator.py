import json
import os
from utils.api_football import obtener_datos_fixture
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.cuotas import obtener_cuotas_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol


def cargar_leagues_ids():
    ruta = os.path.join("utils", "leagues_whitelist_ids.json")
    with open(ruta, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())


def generar_picks_futbol():
    from utils.partidos_disponibles import obtener_partidos_disponibles
    ligas_filtradas = cargar_leagues_ids()
    partidos = obtener_partidos_disponibles(ligas_filtradas)

    for partido in partidos:
        fixture_id = partido['fixture']['id']

        datos_fixture = obtener_datos_fixture(fixture_id)
        if not datos_fixture:
            continue

        stats = obtener_estadisticas_fixture(fixture_id)
        if not stats:
            continue

        cuotas = obtener_cuotas_fixture(fixture_id)
        if not cuotas:
            continue

        pick = analizar_partido_futbol(datos_fixture, stats, cuotas)

        if pick:
            print(f"✅ PICK GENERADO: {pick['pick']} | Cuota: {pick['cuota']} | Motivo: {pick['motivo']}")
        else:
            print(f"❌ Sin valor en el partido: {partido['teams']['home']['name']} vs {partido['teams']['away']['name']}")


if __name__ == "__main__":
    generar_picks_futbol()

