from utils.partidos_disponibles import obtener_partidos_disponibles
from utils.api_football import analizar_partido_futbol
from utils.valor_cuota import filtrar_picks_con_valor
from utils.formato import formatear_mensaje_futbol
from utils.telegram import enviar_mensaje
from utils.horarios import obtener_fecha_actual
from utils.leagues import LEAGUE_NAMES
import datetime


def generar_picks_futbol():
    fecha_actual = obtener_fecha_actual()
    print(f"\nFecha actual: {fecha_actual}")

    picks_finales = []

    for liga_id, temporada in LEAGUE_NAMES.items():
        print(f"\nAnalizando liga {liga_id} - temporada {temporada}")

        partidos = obtener_partidos_disponibles(liga_id=liga_id, fecha=fecha_actual, temporada=temporada)

        for partido in partidos:
            fixture_id = partido['fixture']['id']
            equipo_local = partido['teams']['home']['name']
            equipo_visitante = partido['teams']['away']['name']

            print(f"\nAnalizando partido: {equipo_local} vs {equipo_visitante} (ID: {fixture_id})")

            resultado = analizar_partido_futbol(partido)

            if resultado['valor']:
                mensaje = formatear_mensaje_futbol(
                    fixture_id=fixture_id,
                    equipo_local=equipo_local,
                    equipo_visitante=equipo_visitante,
                    tipo_apuesta=resultado['pick'],
                    cuota=resultado['cuota'],
                    razon=resultado['motivo']
                )
                picks_finales.append({
                    "fixture_id": fixture_id,
                    "liga_id": liga_id,
                    "temporada": temporada,
                    "pick": resultado['pick'],
                    "cuota": resultado['cuota'],
                    "valor": True,
                    "mensaje": mensaje,
                    "timestamp": datetime.datetime.now().isoformat()
                })

    # Enviar los mensajes y filtrar picks con valor real
    picks_filtrados = filtrar_picks_con_valor(picks_finales)
    for pick in picks_filtrados:
        enviar_mensaje(pick['mensaje'], canal="VIP")

    print(f"\n✅ Total picks con valor: {len(picks_filtrados)}")
    return picks_filtrados


if __name__ == "__main__":
    generar_picks_futbol()


