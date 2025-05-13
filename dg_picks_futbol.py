import json
import os
import requests
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

with open("output/team_stats_global.json", encoding="utf-8") as f:
    TEAM_STATS = json.load(f)

def obtener_stats_equipo(nombre):
    for equipo in TEAM_STATS:
        if equipo["Equipo"].lower() == nombre.lower():
            return equipo
    return None

def estimar_resultado(local, visitante):
    stats_local = obtener_stats_equipo(local)
    stats_visitante = obtener_stats_equipo(visitante)

    if not stats_local or not stats_visitante:
        return None

    gf_local = stats_local["Goles a Favor"]
    gc_local = stats_local["Goles en Contra"]
    gf_visit = stats_visitante["Goles a Favor"]
    gc_visit = stats_visitante["Goles en Contra"]

    btts = (stats_local["% BTTS"] + stats_visitante["% BTTS"]) / 2
    over25 = (stats_local["% Over 2.5"] + stats_visitante["% Over 2.5"]) / 2
    prom_goles = (gf_local + gf_visit) / 2

    marcador_estimado = (round((gf_local + gc_visit) / 2), round((gf_visit + gc_local) / 2))

    if marcador_estimado[0] > marcador_estimado[1]:
        pick_ml = f"Gana {local}"
        doble = "1X"
    elif marcador_estimado[1] > marcador_estimado[0]:
        pick_ml = f"Gana {visitante}"
        doble = "X2"
    else:
        pick_ml = "Empate"
        doble = "12"

    if over25 >= 60:
        pick_over = "Over 2.5"
    elif prom_goles >= 1.8:
        pick_over = "Over 1.5"
    elif prom_goles >= 3.2:
        pick_over = "Over 3.5"
    else:
        pick_over = "Under 2.5"

    return {
        "partido": f"{local} vs {visitante}",
        "Promedio Goles": round(prom_goles, 2),
        "% BTTS": round(btts, 1),
        "% Over 2.5": round(over25, 1),
        "Forma Local": stats_local["Últimos 5"],
        "Forma Visitante": stats_visitante["Últimos 5"],
        "Marcador Estimado": f"{marcador_estimado[0]}-{marcador_estimado[1]}",
        "Pick ML": pick_ml,
        "Doble Oportunidad": doble,
        "Línea Goles": pick_over,
        "Comentario": generar_comentario(local, visitante, stats_local, stats_visitante, pick_ml, pick_over)
    }

def generar_comentario(local, visitante, stats_l, stats_v, pick_ml, pick_over):
    comentario = f"{local} promedia {stats_l['Goles a Favor']} goles y {visitante} permite {stats_v['Goles en Contra']}. "
    comentario += f"El pick '{pick_ml}' se respalda en su forma ({stats_l['Últimos 5']}) y tendencia ofensiva. "
    comentario += f"Recomendado '{pick_over}' por el volumen de goles en ambos lados."
    return comentario

def obtener_partidos_del_dia():
    hoy = datetime.today().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    fixtures = []
    for f in data.get("response", []):
        local = f["teams"]["home"]["name"]
        visitante = f["teams"]["away"]["name"]
        fixtures.append((local, visitante))
    return fixtures

# -----------------------------
# Análisis automático completo
# -----------------------------
partidos_del_dia = obtener_partidos_del_dia()

print("\n🧠 Análisis y predicción para los partidos del día:\n")
for local, visitante in partidos_del_dia:
    prediccion = estimar_resultado(local, visitante)
    if prediccion:
        print(f"📊 {prediccion['partido']}")
        print(f"   Promedio Goles: {prediccion['Promedio Goles']}")
        print(f"   % BTTS: {prediccion['% BTTS']}%")
        print(f"   % Over 2.5: {prediccion['% Over 2.5']}%")
        print(f"   Forma {local}: {prediccion['Forma Local']}")
        print(f"   Forma {visitante}: {prediccion['Forma Visitante']}")
        print(f"   🎯 Marcador Estimado: {prediccion['Marcador Estimado']}")
        print(f"   📌 Pick ML: {prediccion['Pick ML']} | Doble oportunidad: {prediccion['Doble Oportunidad']}")
        print(f"   🔥 Línea de Goles: {prediccion['Línea Goles']}")
        print(f"   🧠 Comentario: {prediccion['Comentario']}\n")
    else:
        print(f"⚠️ No hay datos suficientes para {local} vs {visitante}\n")

    time.sleep(1.5)
