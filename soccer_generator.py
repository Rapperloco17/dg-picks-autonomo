import json
from utils.api_football import obtener_partidos_de_liga
from utils.cuotas import obtener_cuota_fixture
from utils.analisar_partido_futbol import analizar_partido_futbol
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.valor_cuota import filtrar_cuotas_con_valor
from utils.telegram import enviar_mensaje
from utils.leagues_whitelist_ids import leagues_ids
from datetime import datetime
import pytz


def generar_picks_futbol():
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    temporada = 2023  # Ajustar si cambia el año en la API
    resultados_finales = []

    for liga_id in leagues_ids:
        try:
            partidos = obtener_partidos_de_liga(liga_id, hoy, temporada)
        except Exception as e:
            print(f"Error al obtener partidos de liga {liga_id}: {e}")
            continue

        for partido in partidos:
            fixture_id = partido["fixture"]["id"]
            equipos = partido["teams"]
            try:
                cuotas = {
                    "over_1.5": obtener_cuota_fixture(fixture_id, "Over/Under 1.5 goals"),
                    "over_2.5": obtener_cuota_fixture(fixture_id, "Over/Under 2.5 goals"),
                    "over_3.5": obtener_cuota_fixture(fixture_id, "Over/Under 3.5 goals"),
                    "under_2.5": obtener_cuota_fixture(fixture_id, "Under 2.5 goals"),
                    "under_3.5": obtener_cuota_fixture(fixture_id, "Under 3.5 goals"),
                    "BTTS": obtener_cuota_fixture(fixture_id, "Both Teams To Score"),
                    "1X": obtener_cuota_fixture(fixture_id, "Double Chance 1X"),
                    "X2": obtener_cuota_fixture(fixture_id, "Double Chance X2"),
                    "12": obtener_cuota_fixture(fixture_id, "Double Chance 12"),
                    "ML_local": obtener_cuota_fixture(fixture_id, "Match Winner - Home"),
                    "ML_visit": obtener_cuota_fixture(fixture_id, "Match Winner - Away"),
                    "Empate": obtener_cuota_fixture(fixture_id, "Match Winner - Draw")
                }

                if all(c is None for c in cuotas.values()):
                    continue

                stats = obtener_estadisticas_fixture(fixture_id)
                pick = analizar_partido_futbol(partido, stats, cuotas)

                if pick and filtrar_cuotas_con_valor(pick["cuota"]):
                    equipos_str = f"{equipos['home']['name']} vs {equipos['away']['name']}"
                    mensaje = f"PARTIDO: {equipos_str}\nPick: {pick['pick']}\nCuota: {pick['cuota']}\nMotivo: {pick['motivo']}\n\u2705 Valor detectado en la cuota"
                    enviar_mensaje(mensaje, canal="VIP")
                    resultados_finales.append(pick)

            except Exception as e:
                print(f"Error al procesar fixture {fixture_id}: {e}")
                continue

    if not resultados_finales:
        print("\u274c No se encontraron picks de valor hoy.")


if __name__ == "__main__":
    generar_picks_futbol()




