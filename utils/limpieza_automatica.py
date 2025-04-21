# utils/limpieza_automatica.py
import os
import time
from datetime import datetime, timedelta

CACHE_DIR = "cache_fixtures"
HIST_DIR = "historial"


def eliminar_archivos_antiguos(directorio, dias=3):
    ahora = time.time()
    eliminados = []

    for archivo in os.listdir(directorio):
        path = os.path.join(directorio, archivo)
        if os.path.isfile(path):
            mod_time = os.path.getmtime(path)
            if ahora - mod_time > dias * 86400:
                os.remove(path)
                eliminados.append(archivo)

    return eliminados


def limpieza_total():
    print("\n🧹 Iniciando limpieza automática de archivos antiguos...")
    cache = eliminar_archivos_antiguos(CACHE_DIR, dias=3)
    historial = eliminar_archivos_antiguos(HIST_DIR, dias=10)

    print(f"🗑️ Cache eliminada: {len(cache)} archivos")
    print(f"📉 Historial eliminado: {len(historial)} archivos")


if __name__ == "__main__":
    limpieza_total()
