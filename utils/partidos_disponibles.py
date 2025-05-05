import requests
import json
import os
from utils.api_football import obtener_partidos_de_liga

# Carga correcta de league_seasons.json
RUTA_LEAGUE_SEASONS = os.path.join(os.path.dirname(__file__), "league_seasons.json")

with open(RUTA_LEAGUE_SEASONS, "r", encoding="utf-8") as f:
    LEAGUE_SEASONS = json.load(f)

def obtener_partidos_disponibles(lista_ligas, fecha):
    todos_los_partidos = []

    for liga_id in lista_ligas:
        temporada = LEAGUE_SEASONS.get(str(liga_id), 2024)  # valor por defecto 2024
        partidos = obtener_partidos_de_liga(liga_id=liga_id, fecha=fecha, temporada=temporada)
        todos_los_partidos.extend(partidos)

    return todos_los_partidos
