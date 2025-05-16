import os
import json
print("🔍 Ejecutando dg_picks_futbol.py")
print("🚀 Ejecutando actualizar_historial.py")
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}

# Ligas válidas (las mismas que en dg_picks_futbol)
ligas_validas = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 41, 42, 43, 45, 46, 47, 48, 49, 50,
    61, 62, 63, 78, 79, 80, 94, 95, 96, 98, 100, 103, 106, 113, 114, 135,
    136, 140, 141, 144, 145, 146, 147, 152, 153, 195, 196, 197, 203, 207,
    208, 210, 235, 239, 244, 253, 257, 262, 263, 265, 268, 271, 281, 345, 357
]

# Ruta donde están los archivos históricos
CARPETA = "historial/unificados"
os.makedirs(CARPETA, exist_ok=True)

# Fecha actual
hoy = datetime.now().date()

for liga_id in ligas_validas:
    liga_nombre = ligas_validas.get(liga_id, f"Liga {liga_id}")
    archivo = os.path.join(CARPETA, f"resultados_{liga_id}.json")

    # Cargar historial actual
    historial = []
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            historial = json.load(f)

    # Obtener la fecha más reciente en el historial
    fechas = [p["fixture"]["date"][:10] for p in historial if "fixture" in p]
    ultima_fecha = max(fechas) if fechas else "2024-01-01"
    fecha_inicio = datetime.strptime(ultima_fecha, "%Y-%m-%d").date() + timedelta(days=1)

    nuevos_partidos = []
    for dias in range((hoy - fecha_inicio).days + 1):
        fecha = (fecha_inicio + timedelta(days=dias)).strftime("%Y-%m-%d")
        url = f"https://v3.football.api-sports.io/fixtures?league={liga_id}&season=2024&date={fecha}"
        res = requests.get(url, headers=HEADERS)
        data = res.json().get("response", [])
        if data:
            print(f"📥 {len(data)} partidos nuevos para {liga_nombre} (ID: {liga_id}) el {fecha}")
            nuevos_partidos.extend(data)

    if nuevos_partidos:
        historial.extend(nuevos_partidos)
        historial.sort(key=lambda x: x["fixture"]["date"])  # Ordenar por fecha
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        print(f"✅ Historial actualizado para {liga_nombre} (ID: {liga_id})")
")
")
    else:
        print(f"⏩ Sin partidos nuevos para {liga_nombre} (ID: {liga_id})")
")

print("🟢 Proceso de actualización completado.")
