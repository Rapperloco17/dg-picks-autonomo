
import json
import os
from datetime import datetime
from utils.api_football import obtener_partidos_de_liga
from utils.soccer_stats import obtener_estadisticas_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.telegram import enviar_mensaje

def generar_picks_futbol():
    from utils.leagues_whitelist_ids import leagues_ids
    from utils.league_seasons import seasons_by_league
    from utils.partidos_disponibles import obtener_fechas_disponibles

    fecha_actual = datetime.utcnow().strftime('%Y-%m-%d')
    fechas = obtener_fechas_disponibles(dias=2)

    todos_los_picks = []

    for fecha in fechas:
        for liga in leagues_ids:
            temporada = seasons_by_league.get(str(liga), 2024)
            try:
                partidos = obtener_partidos_de_liga(liga, fecha, temporada)
            except Exception as e:
                print(f"Error al obtener partidos: {str(e)}")
                continue

            for partido in partidos:
                try:
                    fixture_id = partido["fixture"]["id"]
                    stats, cuotas = obtener_estadisticas_fixture(fixture_id)
                    pick = analizar_partido_futbol(partido, stats, cuotas)

                    if pick:
                        todos_los_picks.append(pick)
                        print(f"✅ PICK: {pick['partido']} | {pick['pick']} | Cuota: {pick['cuota']}")
                        enviar_mensaje(f"PICK DETECTADO 🎯\n\n📍 {pick['partido']}\n💡 {pick['pick']}\n💰 Cuota: {pick['cuota']}\n📊 Motivo: {pick['motivo']}\n\n✅ Valor detectado en la cuota.")

                except Exception as e:
                    print(f"Error procesando fixture {fixture_id}: {str(e)}")

    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(todos_los_picks, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generar_picks_futbol()
