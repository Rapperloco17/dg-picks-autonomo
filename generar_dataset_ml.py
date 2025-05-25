
import os
import json
import pandas as pd
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_ID = "7450739156"
CARPETA = "historial"
ARCHIVO_SALIDA = "dataset_ml_base.json"
archivos = [f for f in os.listdir(CARPETA) if f.startswith("resultados_") and f.endswith(".json")]

data_final = []

for archivo in archivos:
    with open(os.path.join(CARPETA, archivo), "r", encoding="utf-8") as f:
        data = json.load(f)

    for partido in data:
        try:
            local = partido["equipo_local"]
            visitante = partido["equipo_visitante"]
            goles_local = int(partido["goles_local"])
            goles_visitante = int(partido["goles_visitante"])
            fecha = partido.get("fecha", "")
            liga = partido.get("liga", "")

            over_2_5 = 1 if goles_local + goles_visitante > 2.5 else 0
            btts = 1 if goles_local > 0 and goles_visitante > 0 else 0

            data_final.append({
                "fecha": fecha,
                "liga": liga,
                "equipo_local": local,
                "equipo_visitante": visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "over_2_5": over_2_5,
                "btts": btts
            })

        except Exception as e:
            print(f"Error en {archivo}: {e}")

# Guardar JSON localmente
with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f_json:
    json.dump(data_final, f_json, indent=4, ensure_ascii=False)

print("✅ Dataset generado correctamente en dataset_ml_base.json")

# Enviar por Telegram como archivo
if TOKEN and USER_ID:
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(ARCHIVO_SALIDA, "rb") as file:
        response = requests.post(
            url,
            data={"chat_id": USER_ID},
            files={"document": file},
            timeout=30
        )
    if response.status_code == 200:
        print("✅ Archivo enviado por Telegram con éxito.")
    else:
        print(f"⚠️ Error al enviar por Telegram: {response.text}")
