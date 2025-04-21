# utils/historial_picks.py
import os
import json
from datetime import datetime

HIST_DIR = "historial"
os.makedirs(HIST_DIR, exist_ok=True)


def guardar_pick_en_historial(pick):
    fecha = datetime.now().strftime("%Y-%m-%d")
    archivo = os.path.join(HIST_DIR, f"{fecha}.json")

    historial = []
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            historial = json.load(f)

    historial.append(pick)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def mostrar_historial_del_dia():
    fecha = datetime.now().strftime("%Y-%m-%d")
    archivo = os.path.join(HIST_DIR, f"{fecha}.json")
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
