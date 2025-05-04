from utils.leagues_whitelist_ids import LEAGUES_WHITELIST
from utils.league_seasons import LEAGUE_SEASONS
from utils.api_football import obtener_partidos_de_liga
from datetime import datetime

def obtener_partidos_disponibles(fecha_str):
    """
    Revisa todas las ligas permitidas y obtiene los partidos disponibles desde la API-FOOTBALL para la fecha dada.
    """

    partidos_disponibles = []

    for liga_id in LEAGUES_WHITELIST:
        temporada = LEAGUE_SEASONS.get(str(liga_id), 2024)

        partidos = obtener_partidos_de_liga(liga_id, fecha_str, temporada)

        for p in partidos:
            fixture_id = p["fixture"]["id"]
            equipo_local = p["teams"]["home"]["name"]
            equipo_visitante = p["teams"]["away"]["name"]
            fecha_partido = p["fixture"]["date"]

            partidos_disponibles.append({
                "fixture_id": fixture_id,
                "fecha": fecha_partido,
                "liga_id": liga_id,
                "temporada": temporada,
                "equipo_local": equipo_local,
                "equipo_visitante": equipo_visitante
            })

    return partidos_disponibles
