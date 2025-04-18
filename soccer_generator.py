import os
import json
from datetime import datetime

OUTPUT_FOLDER = "outputs/"


def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def generate_soccer_picks():
    print("Iniciando generación de picks de fútbol...")

    # Ejemplo de partidos
    partidos = [
        {"partido": "Barcelona vs Real Madrid", "cuota": 1.90, "valor": True},
        {"partido": "Manchester City vs Arsenal", "cuota": 2.10, "valor": False}
    ]

    print(f"Partidos obtenidos: {len(partidos)}")

    picks = []
    for p in partidos:
        if p["valor"]:
            pick = {
                "partido": p["partido"],
                "cuota": p["cuota"],
                "valor": p["valor"],
                "fecha": datetime.now().strftime("%Y-%m-%d")
            }
            picks.append(pick)

    data = {"picks": picks}
    nombre_archivo = f"futbol_{datetime.now().strftime('%Y-%m-%d')}.json"
    ruta_archivo = os.path.join(OUTPUT_FOLDER, nombre_archivo)
    save_json(data, ruta_archivo)
    print(f"Picks guardados en {ruta_archivo}")


if __name__ == "__main__":
    generate_soccer_picks()
