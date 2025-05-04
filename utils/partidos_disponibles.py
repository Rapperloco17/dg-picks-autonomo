from utils.api_football import get_fixtures_by_league_and_date
from utils.leagues import obtener_ligas_hoy
from utils.league_seasons import obtener_temporada_actual
from datetime import datetime

def obtener_partidos_disponibles(fecha_actual=None):
    if fecha_actual is None:
        fecha_actual = datetime.now().strftime('%Y-%m-%d')

    ligas = obtener_ligas_hoy()
    partidos_disponibles = []

    for liga in ligas:
        temporada = obtener_temporada_actual(liga)
        fixtures = get_fixtures_by_league_and_date(liga, temporada, fecha_actual)
        partidos_disponibles.extend(fixtures)

    return partidos_disponibles
