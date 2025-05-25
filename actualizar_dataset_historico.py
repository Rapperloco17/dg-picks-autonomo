
import requests
import os
import json
import datetime
from entrenar_modelo_ml import enviar_por_telegram
from entrenar_modelo_ml import entrenar_modelos

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

def cargar_dataset():
    try:
        with open("input/dataset_ml_base.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def guardar_dataset(data):
    with open("input/dataset_ml_base.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ya_existe(partido, dataset):
    return any(
        p["fecha"] == partido["fecha"] and
        p["liga"] == partido["liga"] and
        p["local"] == partido["local"] and
        p["visitante"] == partido["visitante"]
        for p in dataset
    )

def formatear_partido(f):
    goles_local = f["goals"]["home"]
    goles_visitante = f["goals"]["away"]
    return {
        "fecha": f["fixture"]["date"][:10],
        "liga": f["league"]["name"],
        "local": f["teams"]["home"]["name"],
        "visitante": f["teams"]["away"]["name"],
        "goles_local": goles_local,
        "goles_visitante": goles_visitante,
        "btts": int(goles_local > 0 and goles_visitante > 0),
        "over_2_5": int((goles_local + goles_visitante) > 2.5),
        "resultado": "local" if goles_local > goles_visitante else "visitante" if goles_local < goles_visitante else "empate"
    }

def actualizar():
    dataset = cargar_dataset()
    nuevos = []
    hoy = datetime.datetime.utcnow().date()
    for dias_atras in range(0, 11):  # Desde 14 mayo hasta hoy
        fecha = hoy - datetime.timedelta(days=dias_atras)
        for liga_id in LIGAS_VALIDAS:
            res = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params={
                "league": liga_id,
                "season": 2024,
                "date": fecha,
                "status": "FT"
            })
            if res.status_code != 200:
                continue
            partidos = res.json().get("response", [])
            for f in partidos:
                partido = formatear_partido(f)
                if not ya_existe(partido, dataset):
                    dataset.append(partido)
                    nuevos.append(partido)

    guardar_dataset(dataset)
    print(f"✅ Dataset actualizado con {len(nuevos)} partidos nuevos.")
    enviar_por_telegram("input/dataset_ml_base.json")

    # Entrenar de nuevo
    entrenar_modelos()

actualizar()
