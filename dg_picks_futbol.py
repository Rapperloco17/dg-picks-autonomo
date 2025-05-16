# dg_picks_futbol.py — Análisis de partidos con historial real
import os
import json
import requests
from datetime import datetime

# Lista exacta de League IDs desde 'lista definitiva.xlsx'
ligas_activas_ids = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88,
    94, 103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143,
    144, 162, 164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242,
    244, 253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

# Ruta a la carpeta de historiales unificados
historial_folder = "historial/unificados"

# Cargar historiales por liga
historico_por_liga = {}
for league_id in ligas_activas_ids:
    archivo = f"resultados_{league_id}.json"
    ruta_json = os.path.join(historial_folder, archivo)
    if os.path.exists(ruta_json):
        with open(ruta_json, "r", encoding="utf-8") as f:
            historico_por_liga[league_id] = json.load(f)

# Obtener partidos del día desde la API
API_KEY = os.getenv("API_FOOTBALL_KEY") or "TU_API_KEY_AQUI"
headers = {"x-apisports-key": API_KEY}
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
url = f"https://v3.football.api-sports.io/fixtures?date={fecha_hoy}"
response = requests.get(url, headers=headers)
data = response.json()
fixtures = data.get("response", [])

# Analizar partidos que tengan historial
for fixture in fixtures:
    league_id = fixture["league"]["id"]
    if league_id not in historico_por_liga:
        continue

    equipo_local = fixture["teams"]["home"]["name"]
    equipo_visita = fixture["teams"]["away"]["name"]

    historial = historico_por_liga[league_id]
    partidos = historial["response"]

    # Filtrar partidos previos de cada equipo
    prev_local = [p for p in partidos if p["teams"]["home"]["name"] == equipo_local or p["teams"]["away"]["name"] == equipo_local]
    prev_visita = [p for p in partidos if p["teams"]["home"]["name"] == equipo_visita or p["teams"]["away"]["name"] == equipo_visita]

    def calcular_promedios(partidos, equipo):
        goles_a_favor = []
        goles_en_contra = []
        for p in partidos:
            local = p["teams"]["home"]["name"]
            visita = p["teams"]["away"]["name"]
            goles_local = p["goals"]["home"]
            goles_visita = p["goals"]["away"]
            if local == equipo:
                goles_a_favor.append(goles_local)
                goles_en_contra.append(goles_visita)
            elif visita == equipo:
                goles_a_favor.append(goles_visita)
                goles_en_contra.append(goles_local)
        prom_favor = round(sum(goles_a_favor)/len(goles_a_favor), 2) if goles_a_favor else 0
        prom_contra = round(sum(goles_en_contra)/len(goles_en_contra), 2) if goles_en_contra else 0
        return prom_favor, prom_contra

    gf_local, gc_local = calcular_promedios(prev_local, equipo_local)
    gf_visita, gc_visita = calcular_promedios(prev_visita, equipo_visita)

    print(f"\n📊 {equipo_local} vs {equipo_visita}")
    print(f"Promedio goles {equipo_local}: {gf_local} GF / {gc_local} GC")
    print(f"Promedio goles {equipo_visita}: {gf_visita} GF / {gc_visita} GC")

# 🔄 Próximo paso: cálculo BTTS, Over 2.5, forma reciente y predicción de pick
