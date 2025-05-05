import json
import os
from utils.api_football import obtener_partidos_de_liga
from utils.league_seasons import LEAGUE_SEASONS

# ✅ Cargar archivo JSON con los IDs de ligas permitidas
def cargar_leagues_whitelist_ids():
    ruta = os.path.join(os.path.dirname(__file__), 'leagues_whitelist_ids.json')
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

LEAGUES_WHITELIST = cargar_leagues_whitelist_ids()


def obtener_partidos_disponibles(fecha):
    partidos_disponibles = []

    for liga_id in LEAGUES_WHITELIST:
        temporada = LEAGUE_SEASONS.get(str(liga_id), 2024)
        print(f"🔍 Analizando liga {liga_id} - temporada {temporada}")

        try:
            partidos_liga = obtener_partidos_de_liga(liga_id, fecha, temporada)
            if partidos_liga:
                partidos_disponibles.extend(partidos_liga)
        except Exception as e:
            print(f"❌ Error obteniendo partidos de liga {liga_id}: {str(e)}")

    return partidos_disponibles
