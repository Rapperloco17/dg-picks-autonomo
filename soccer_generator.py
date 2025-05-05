import json
from utils.partidos_disponibles import obtener_partidos_disponibles
from utils.api_football import obtener_datos_fixture
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.cuotas import obtener_cuotas_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.telegram import enviar_mensaje

def generar_picks_soccer():
    print("🔍 Buscando partidos de fútbol...")

    partidos = obtener_partidos_disponibles()
    print(f"📅 Total de partidos encontrados: {len(partidos)}")

    for fixture in partidos:
        fixture_id = fixture["fixture"]["id"]
        nombre_partido = f'{fixture["teams"]["home"]["name"]} vs {fixture["teams"]["away"]["name"]}'
        print(f"\n⚽ Analizando: {nombre_partido} (ID: {fixture_id})")

        datos = obtener_datos_fixture(fixture_id)
        stats = obtener_estadisticas_fixture(fixture_id)
        cuotas = obtener_cuotas_fixture(fixture_id)

        if not datos or not stats or not cuotas:
            print("⚠️ Datos incompletos. Se omite el partido.")
            continue

        pick = analizar_partido_futbol(datos, stats, cuotas)

        if pick:
            mensaje = (
                f"📊 *Pick de Fútbol Detectado:*\n\n"
                f"📍 Partido: {nombre_partido}\n"
                f"✅ Apuesta: *{pick['pick']}*\n"
                f"💡 Motivo: {pick['motivo']}\n"
                f"💸 Cuota: {pick['cuota']}\n\n"
                f"📘 Análisis automatizado por DG Picks\n"
                f"✅ Valor detectado en la cuota"
            )
            enviar_mensaje(mensaje, canal="VIP")

if __name__ == "__main__":
    generar_picks_soccer()
