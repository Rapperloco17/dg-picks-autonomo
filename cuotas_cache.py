
# utils/cuotas_cache.py

import json
import os
from datetime import datetime
from utils.cuotas import obtener_cuota_bet365

CACHE_FILE = "cuotas_cache.json"

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, "w") as file:
        json.dump(cache, file)

def get_cuota_cached(evento, mercado, deporte):
    cache = cargar_cache()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    clave = f"{fecha_hoy}|{deporte}|{evento}|{mercado}"

    if clave in cache:
        return cache[clave]

    cuota = obtener_cuota_bet365(deporte, mercado)
    if cuota:
        cache[clave] = cuota
        guardar_cache(cache)
    return cuota
