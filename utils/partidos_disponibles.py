# utils/partidos_disponibles.py

from utils.odds_api import obtener_fixtures
from utils.leagues_whitelist_ids import leagues_whitelist
from utils.league_seasons import league_seasons
from datetime import datetime

def obtener_partidos_disponibles(fecha_actual):
    fixtures_disponibles = []

    for liga_id in leagues_whitelist:
        temporada = league_seasons.get(str(liga_id))
        if not temporada:
            continue

        try:
            partidos = obtener_fixtures(liga_id, temporada, fecha_actual)
            for partido in partidos:
                fixture_id = partido.get("fixture", {}).get("id")
                if fixture_id:
                    fixtures_disponibles.append({
                        "fixture_id": fixture_id,
                        "liga_id": liga_id,
                        "temporada": temporada
                    })
        except Exception as e:
            print(f"Error al obtener fixtures de liga {liga_id}: {e}")

    return fixtures_disponibles
