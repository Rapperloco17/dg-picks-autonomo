import json
from utils.api_football import obtener_partidos_de_liga
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.cuotas import obtener_cuota_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.leagues_whitelist_ids import LEAGUES_WHITELIST
from datetime import datetime


def generar_picks_futbol():
    hoy = datetime.now().strftime('%Y-%m-%d')
    temporada = 2024
    todos_los_picks = []

    print(f"\nBuscando partidos para el día {hoy}...\n")

    for league_id in LEAGUES_WHITELIST:
        try:
            print(f"\n--- Procesando liga ID {league_id} ---")
            partidos = obtener_partidos_de_liga(league_id, hoy, temporada)

            if not partidos:
                print("Sin partidos en esta liga.")
                continue

            for partido in partidos:
                fixture = partido["fixture"]
                fixture_id = fixture["id"]

                stats = obtener_estadisticas_fixture(fixture_id)
                cuotas = {
                    "over_1.5": obtener_cuota_fixture(fixture_id, "Over 1.5 goals"),
                    "over_2.5": obtener_cuota_fixture(fixture_id, "Over 2.5 goals"),
                    "under_2.5": obtener_cuota_fixture(fixture_id, "Under 2.5 goals"),
                    "BTTS": obtener_cuota_fixture(fixture_id, "Both Teams To Score"),
                    "1X": obtener_cuota_fixture(fixture_id, "1X"),
                    "X2": obtener_cuota_fixture(fixture_id, "X2"),
                    "12": obtener_cuota_fixture(fixture_id, "12"),
                    "ML_local": obtener_cuota_fixture(fixture_id, "Match Winner - 1"),
                    "ML_visit": obtener_cuota_fixture(fixture_id, "Match Winner - 2"),
                    "Empate": obtener_cuota_fixture(fixture_id, "Match Winner - X")
                }

                pick = analizar_partido_futbol(partido, stats, cuotas)

                if pick:
                    print(f"\n✅ PICK DETECTADO")
                    print(f"Partido: {pick['partido']}")
                    print(f"Pick: {pick['pick']}")
                    print(f"Cuota: {pick['cuota']}")
                    print(f"Motivo: {pick['motivo']}\n")
                    todos_los_picks.append(pick)

        except Exception as e:
            print(f"Error en liga {league_id}: {str(e)}")

    if not todos_los_picks:
        print("\nNo se encontraron picks con valor para hoy.\n")
    else:
        print(f"\n--- TOTAL PICKS DETECTADOS: {len(todos_los_picks)} ---\n")

    return todos_los_picks
