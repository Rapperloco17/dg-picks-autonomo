from utils.api_football import obtener_partidos_de_liga
from utils.leagues_whitelist_ids import leagues_ids
from utils.valor_cuota import filtrar_cuotas_con_valor
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.analizar_partido_futbol import analizar_partido
from utils.cuotas import obtener_cuota_fixture
from utils.telegram import enviar_mensaje

from datetime import datetime
import pytz

def generar_picks_futbol():
    zona_horaria = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(zona_horaria).strftime('%Y-%m-%d')
    temporada = "2024"

    partidos_filtrados = []

    for liga_id in leagues_ids:
        partidos = obtener_partidos_de_liga(liga_id, hoy, temporada)

        for partido in partidos:
            fixture_id = partido['fixture']['id']
            estadisticas = obtener_estadisticas_fixture(fixture_id)

            if estadisticas:
                analisis = analizar_partido(estadisticas)
                if analisis.get("valor_detectado"):
                    cuota = obtener_cuota_fixture(fixture_id)
                    if cuota:
                        partido_final = {
                            "partido": f"{partido['teams']['home']['name']} vs {partido['teams']['away']['name']}",
                            "fecha": partido['fixture']['date'],
                            "liga": partido['league']['id'],
                            "analisis": analisis,
                            "cuota": cuota
                        }
                        partidos_filtrados.append(partido_final)

    picks_filtrados = filtrar_cuotas_con_valor(partidos_filtrados)

    for pick in picks_filtrados:
        mensaje = (
            f"⚽️ Partido: {pick['partido']}\n"
            f"📊 Análisis: {pick['analisis']['resumen']}\n"
            f"💸 Cuota: {pick['cuota']}\n"
            f"✅ Valor detectado en la cuota"
        )
        enviar_mensaje(mensaje)

if __name__ == "__main__":
    generar_picks_futbol()


