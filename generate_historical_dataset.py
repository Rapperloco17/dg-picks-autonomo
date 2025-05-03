import os
import json
import time
from datetime import datetime
from utils.api_football import API_KEY, API_URL
import requests

# ⚙️ Leer ligas y temporadas desde JSON
with open("utils/leagues_whitelist_ids.json") as f:
    LIGAS = json.load(f)["allowed_league_ids"]

with open("utils/league_seasons.json") as f:
    TEMPORADAS = json.load(f)

# 📁 Crear carpeta si no existe
os.makedirs("historial/dataset_historico", exist_ok=True)

# 🔐 Headers para la API
headers = {
    "x-apisports-key": API_KEY
}

# 🧠 Recolectar datos por liga y temporada
historico = []

for liga_id in LIGAS:
    for temporada in TEMPORADAS.get(str(liga_id), []):
        print(f"📊 Consultando liga {liga_id} - temporada {temporada}")
        try:
            url = f"{API_URL}/fixtures?league={liga_id}&season={temporada}"
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data = res.json().get("response", [])

            for fixture in data:
                fdata = fixture["fixture"]
                teams = fixture["teams"]
                goals = fixture["goals"]
                league = fixture["league"]

                historico.append({
                    "fixture_id": fdata["id"],
                    "fecha": fdata["date"],
                    "liga_id": league["id"],
                    "liga_nombre": league["name"],
                    "temporada": temporada,
                    "equipo_local": teams["home"]["name"],
                    "equipo_visitante": teams["away"]["name"],
                    "goles_local": goals["home"],
                    "goles_visitante": goals["away"],
                    "estado": fdata["status"]["short"]
                })

            print(f"✅ {len(data)} partidos agregados de {league['name']} {temporada}")
            time.sleep(1.2)  # Evitar saturar API

        except Exception as e:
            print(f"❌ Error en liga {liga_id} temporada {temporada}: {e}")

# 💾 Guardar resultado
fecha = datetime.now().strftime("%Y-%m-%d")
ruta_json = f"historial/dataset_historico/historico_{fecha}.json"

with open(ruta_json, "w", encoding="utf-8") as f:
    json.dump(historico, f, ensure_ascii=False, indent=4)

print(f"\n📁 Dataset histórico guardado en: {ruta_json}")
print(f"📌 Total partidos recopilados: {len(historico)}")
