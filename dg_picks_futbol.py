# dg_picks_futbol.py — Versión completa con aviso si no hay partidos válidos
import os
import json
from datetime import datetime
import requests

# --- Lista definitiva de League IDs válidos ---
ligas_activas_ids = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88,
    94, 103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143,
    144, 162, 164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242,
    244, 253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

# --- Cargar historiales locales ---
historial_folder = "historial/unificados"
historico_por_liga = {}

for league_id in ligas_activas_ids:
    archivo = f"resultados_{league_id}.json"
    ruta_json = os.path.join(historial_folder, archivo)
    if os.path.exists(ruta_json):
        with open(ruta_json, "r", encoding="utf-8") as f:
            historico_por_liga[league_id] = json.load(f)

# --- Obtener partidos del día desde API-Football ---
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
headers = {"x-apisports-key": API_KEY}
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
url = f"https://v3.football.api-sports.io/fixtures?date={fecha_hoy}"
response = requests.get(url, headers=headers)
data = response.json()
fixtures = [f for f in data.get("response", []) if f["fixture"]["status"]["short"] == "NS"]

# --- Mostrar SOLO partidos en ligas activas con historial ---
print(f"
📆 Partidos válidos en ligas activas con historial:
")
for f in fixtures:
    lid = f["league"]["id"]
    if lid in historico_por_liga:
        local = f["teams"]["home"]["name"]
        visita = f["teams"]["away"]["name"]
        liga = f["league"]["name"]
        print(f"{local} vs {visita} — {liga} (ID: {lid})")

# --- Analizar partidos válidos con historial ---
hay_partidos_validos = False

for fixture in fixtures:
    league_id = fixture["league"]["id"]
    if league_id not in historico_por_liga:
        continue

    equipo_local = fixture["teams"]["home"]["name"]
    equipo_visita = fixture["teams"]["away"]["name"]
    partidos = historico_por_liga[league_id]["response"]

    prev_local = [p for p in partidos if equipo_local in (p["teams"]["home"]["name"], p["teams"]["away"]["name"])]
    prev_visita = [p for p in partidos if equipo_visita in (p["teams"]["home"]["name"], p["teams"]["away"]["name"])]

    def calcular_promedios(partidos, equipo):
        gf, gc = [], []
        for p in partidos:
            h, a = p["teams"]["home"]["name"], p["teams"]["away"]["name"]
            gh, ga = p["goals"]["home"], p["goals"]["away"]
            if h == equipo:
                gf.append(gh)
                gc.append(ga)
            elif a == equipo:
                gf.append(ga)
                gc.append(gh)
        return round(sum(gf)/len(gf), 2), round(sum(gc)/len(gc), 2)

    def calcular_forma(partidos, equipo):
        ultimos = [p for p in partidos if (
            p["teams"]["home"]["name"] == equipo or p["teams"]["away"]["name"] == equipo
        ) and p["goals"]["home"] is not None and p["goals"]["away"] is not None][-5:]
        puntos = 0
        for p in ultimos:
            h = p["teams"]["home"]["name"]
            a = p["teams"]["away"]["name"]
            gh = p["goals"]["home"]
            ga = p["goals"]["away"]
            if equipo == h and gh > ga:
                puntos += 3
            elif equipo == a and ga > gh:
                puntos += 3
            elif ga == gh:
                puntos += 1
        return puntos

    def calcular_btts_over(partidos, equipo):
        btts_count = 0
        over_count = 0
        jugados = 0
        for p in partidos:
            gh = p["goals"]["home"]
            ga = p["goals"]["away"]
            if gh is None or ga is None:
                continue
            jugados += 1
            if gh > 0 and ga > 0:
                btts_count += 1
            if (gh + ga) >= 3:
                over_count += 1
        btts_pct = round((btts_count / jugados) * 100, 1) if jugados else 0
        over_pct = round((over_count / jugados) * 100, 1) if jugados else 0
        return btts_pct, over_pct

    gf_local, gc_local = calcular_promedios(prev_local, equipo_local)
    gf_visita, gc_visita = calcular_promedios(prev_visita, equipo_visita)
    forma_local = calcular_forma(prev_local, equipo_local)
    forma_visita = calcular_forma(prev_visita, equipo_visita)
    btts_local, over_local = calcular_btts_over(prev_local, equipo_local)
    btts_visita, over_visita = calcular_btts_over(prev_visita, equipo_visita)

    print(f"\n📊 {equipo_local} vs {equipo_visita}")
    print(f"Promedio goles {equipo_local}: {gf_local} GF / {gc_local} GC")
    print(f"Promedio goles {equipo_visita}: {gf_visita} GF / {gc_visita} GC")
    print(f"Forma reciente {equipo_local}: {forma_local} pts (últimos 5)")
    print(f"Forma reciente {equipo_visita}: {forma_visita} pts (últimos 5)")
    print(f"BTTS %: {equipo_local} = {btts_local}%, {equipo_visita} = {btts_visita}%")
    print(f"Over 2.5 %: {equipo_local} = {over_local}%, {equipo_visita} = {over_visita}%")

    sugerencia = None
    if btts_local > 60 and btts_visita > 60:
        sugerencia = "Ambos anotan (BTTS)"
    elif over_local > 60 and over_visita > 60:
        sugerencia = "Over 2.5 goles"
    elif gf_local > 1.5 and gc_visita > 1.2:
        sugerencia = f"Gana {equipo_local}"
    elif gf_visita > 1.5 and gc_local > 1.2:
        sugerencia = f"Gana {equipo_visita}"

    if sugerencia:
        print(f"🎯 Pick sugerido: {sugerencia}")
    else:
        print("❌ Sin pick claro basado en datos")

    print("✅ Análisis completo para este partido\n")
    hay_partidos_validos = True

# --- Mensaje si no hubo partidos válidos ---
if not hay_partidos_validos:
    print("⚠️ Hoy no hubo partidos válidos con historial para analizar.")
