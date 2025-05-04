import datetime
from utils.api_football import obtener_partidos_de_liga
from utils.leagues_whitelist_ids import LEAGUES_WHITELIST
from utils.league_seasons import LEAGUE_SEASONS

def obtener_partidos_disponibles():
    hoy = datetime.date.today()
    partidos_disponibles = []

    for liga_id in LEAGUES_WHITELIST:
        temporada = LEAGUE_SEASONS.get(str(liga_id), hoy.year)

        try:
            fixtures = obtener_partidos_de_liga(liga_id=liga_id, fecha=hoy.isoformat(), temporada=temporada)
            if isinstance(fixtures, list):
                partidos_disponibles.extend(fixtures)
        except Exception as e:
            print(f"Error al obtener partidos para liga {liga_id}: {str(e)}")

    return partidos_disponibles
