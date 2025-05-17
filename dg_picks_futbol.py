import requests
import json
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"
    headers = {
        "x-apisports-key": API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        partidos = data.get("response", [])
        print(f"✅ Se obtuvieron {len(partidos)} partidos desde la API-FOOTBALL para hoy ({hoy})")
        return partidos
    except Exception as e:
        print(f"⚠️ Error al obtener partidos de la API: {e}")
        return []

def calcular_stats(equipo, partidos):
    goles_favor = []
    goles_contra = []
    btts = []
    over25 = []

    for p in partidos:
        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")
        goles_local = p.get("goles_local")
        goles_visitante = p.get("goles_visitante")

        if local is None or visitante is None or goles_local is None or goles_visitante is None:
            continue

        if equipo == local:
            gf = goles_local
            gc = goles_visitante
        elif equipo == visitante:
            gf = goles_visitante
            gc = goles_local
        else:
            continue

        goles_favor.append(gf)
        goles_contra.append(gc)
        btts.append(1 if goles_local > 0 and goles_visitante > 0 else 0)
        over25.append(1 if goles_local + goles_visitante > 2.5 else 0)

    total = len(goles_favor)
    if total == 0:
        return {"juegos": 0, "goles_favor": 0, "goles_contra": 0, "btts_pct": 0, "over25_pct": 0}

    return {
        "juegos": total,
        "goles_favor": sum(goles_favor) / total,
        "goles_contra": sum(goles_contra) / total,
        "btts_pct": 100 * sum(btts) / total,
        "over25_pct": 100 * sum(over25) / total
    }

# ================= EJECUCIÓN =====================

partidos = obtener_fixtures_hoy()

if not partidos:
    print("⚠️ No se encontraron partidos para hoy. Verifica la API o la fecha.")
    exit()

for fixture in partidos:
    fixture_id = fixture.get("fixture", {}).get("id")
    equipos = fixture.get("teams", {})
    nombre_local = equipos.get("home", {}).get("name")
    nombre_visitante = equipos.get("away", {}).get("name")

    print(f"\n📊 Analizando: {nombre_local} vs {nombre_visitante} (Fixture ID: {fixture_id})")

    # Aquí continuarías con tu lógica personalizada (descargar resultados históricos, análisis, predicciones, etc.)
    # Este bloque es sólo un inicio del flujo de trabajo automatizado
