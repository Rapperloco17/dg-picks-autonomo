import requests
import json
from datetime import datetime
import unicodedata

# --- Normalizar nombres de equipo ---
def normalizar(nombre):
    nombre = nombre.lower().replace(".", "").replace("'", "").replace("-", "").replace("’", "")
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("utf-8")
    return nombre.replace(" ", "")

# --- Cargar historial por liga ---
historico_por_liga = {}
import os
import glob
files = glob.glob("historial/unificados/resultados_*.json")
for file in files:
    lid = int(file.split("_")[-1].replace(".json", ""))
    with open(file, "r", encoding="utf-8") as f:
        historico_por_liga[lid] = json.load(f)

# --- Fecha actual ---
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# --- Obtener partidos del día desde API ---
url = f"https://v3.football.api-sports.io/fixtures?date={fecha_hoy}"
headers = {
    "x-apisports-key": "TU_API_KEY_AQUI"
}
response = requests.get(url, headers=headers)
data = response.json()
fixtures = [f for f in data.get("response", []) if f["fixture"]["status"]["short"] == "NS"]

print("📆 Partidos válidos en ligas activas con historial:\n")
partidos_validos = []
for f in fixtures:
    lid = f["league"]["id"]
    if lid in historico_por_liga:
        local = f["teams"]["home"]["name"]
        visita = f["teams"]["away"]["name"]
        liga = f["league"]["name"]
        print(f"{local} vs {visita} — {liga} (ID: {lid})")
        partidos_validos.append((f, lid))

if not partidos_validos:
    print("⚠️ Hoy no hubo partidos válidos con historial para analizar.")
    exit()

# --- Funciones para cálculo ---
def calcular_promedios(partidos, equipo):
    gf = gc = 0
    for p in partidos:
        if equipo in p["teams"]["home"]["name"]:
            gf += p["goals"]["home"]
            gc += p["goals"]["away"]
        else:
            gf += p["goals"]["away"]
            gc += p["goals"]["home"]
    pj = len(partidos)
    return round(gf / pj, 2), round(gc / pj, 2)

def calcular_forma(partidos, equipo):
    puntos = 0
    for p in partidos[-5:]:
        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]
        gh = p["goals"]["home"]
        ga = p["goals"]["away"]
        if equipo in home:
            if gh > ga:
                puntos += 3
            elif gh == ga:
                puntos += 1
        elif equipo in away:
            if ga > gh:
                puntos += 3
            elif gh == ga:
                puntos += 1
    return puntos

def calcular_bttover(partidos, equipo):
    btts = over = 0
    for p in partidos:
        g1 = p["goals"]["home"]
        g2 = p["goals"]["away"]
        if g1 >= 0 and g2 >= 0:
            if g1 >= 2 or g2 >= 2:
                over += 1
            if g1 > 0 and g2 > 0:
                btts += 1
    total = len(partidos)
    return round((btts / total) * 100, 1), round((over / total) * 100, 1)

# --- Análisis ---
for fixture, lid in partidos_validos:
    equipo_local = fixture["teams"]["home"]["name"]
    equipo_visita = fixture["teams"]["away"]["name"]
    partidos = historico_por_liga[lid]

    equipo_local_norm = normalizar(equipo_local)
    equipo_visita_norm = normalizar(equipo_visita)

    prev_local = [p for p in partidos if equipo_local_norm in normalizar(p["teams"]["home"]["name"]) or equipo_local_norm in normalizar(p["teams"]["away"]["name"]) ]
    prev_visita = [p for p in partidos if equipo_visita_norm in normalizar(p["teams"]["home"]["name"]) or equipo_visita_norm in normalizar(p["teams"]["away"]["name"]) ]

    if not prev_local or not prev_visita:
        print(f"⚠️ Sin historial suficiente para: {equipo_local} o {equipo_visita}\n")
        continue

    gf_l, gc_l = calcular_promedios(prev_local, equipo_local)
    gf_v, gc_v = calcular_promedios(prev_visita, equipo_visita)
    forma_l = calcular_forma(prev_local, equipo_local)
    forma_v = calcular_forma(prev_visita, equipo_visita)
    btts_l, over_l = calcular_bttover(prev_local, equipo_local)
    btts_v, over_v = calcular_bttover(prev_visita, equipo_visita)

    print(f"\n📊 {equipo_local} vs {equipo_visita}")
    print(f"Promedio goles {equipo_local}: {gf_l} GF / {gc_l} GC")
    print(f"Promedio goles {equipo_visita}: {gf_v} GF / {gc_v} GC")
    print(f"Forma reciente {equipo_local}: {forma_l} pts (últimos 5)")
    print(f"Forma reciente {equipo_visita}: {forma_v} pts (últimos 5)")
    print(f"BTTS %: {equipo_local} = {btts_l}%, {equipo_visita} = {btts_v}%")
    print(f"Over 2.5 %: {equipo_local} = {over_l}%, {equipo_visita} = {over_v}%")

    sugerencia = "Sin pick claro basado en datos"
    if btts_l > 60 and btts_v > 60:
        sugerencia = "Ambos anotan (BTTS)"
    elif over_l > 60 and over_v > 60:
        sugerencia = "Over 2.5 goles"
    elif gf_l > 1.5 and gc_v > 1.2:
        sugerencia = f"Gana {equipo_local}"
    elif gf_v > 1.5 and gc_l > 1.2:
        sugerencia = f"Gana {equipo_visita}"

    print(f"🎯 Pick sugerido: {sugerencia}")
    print("✅ Análisis completo para este partido\n")
