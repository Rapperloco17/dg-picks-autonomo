from utils.api_football import obtener_datos_fixture
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.valor_cuota import filtrar_cuotas_con_valor
from utils.leagues_whitelist_ids import leagues_ids
from utils.partidos_disponibles import obtener_partidos_disponibles
from utils.telegram import enviar_mensaje
import datetime


def generar_picks_futbol():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    fixtures = obtener_partidos_disponibles(leagues_ids, hoy)

    print(f"🔎 {len(fixtures)} partidos disponibles para analizar")

    for fixture in fixtures:
        fixture_id = fixture["fixture"]["id"]
        datos = obtener_datos_fixture(fixture_id)
        stats = obtener_estadisticas_fixture(fixture_id)
        cuotas_filtradas = filtrar_cuotas_con_valor(fixture_id)

        if not datos or not stats or not cuotas_filtradas:
            continue

        pick = analizar_partido_futbol(datos, stats, cuotas_filtradas)

        if pick:
            mensaje = f"⚽️ *{pick['partido']}*\n\nPick: {pick['pick']}\nCuota: {pick['cuota']}\nMotivo: {pick['motivo']}\n\n✅ Valor detectado en la cuota"
            enviar_mensaje(mensaje, canal="futbol")

