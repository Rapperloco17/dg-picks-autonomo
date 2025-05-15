import os
import json
import datetime
import requests
import re
import glob
import statistics
import random

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

RUTA_HISTORIAL = "historial/unificados"
API_URL = "https://v3.football.api-sports.io"

# Cargar historial
historial = {}
archivos_json = glob.glob(f"{RUTA_HISTORIAL}/resultados_*.json")
for archivo in archivos_json:
    clave = os.path.basename(archivo).replace("resultados_", "").replace(".json", "")
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            historial[clave] = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {clave}: {e}")

# Forma y goles
def calcular_stats_equipo(juegos, equipo, condicion):
    gf, gc, btts, over25, resultados = [], [], 0, 0, []
    for partido in juegos[-20:]:
        try:
            h = partido['teams']['home']['name']
            a = partido['teams']['away']['name']
            g_h = partido['goals']['home']
            g_a = partido['goals']['away']
            if g_h is None or g_a is None:
                continue
            if condicion == 'local' and h == equipo:
                gf.append(g_h)
                gc.append(g_a)
                if g_h > 0 and g_a > 0: btts += 1
                if (g_h + g_a) >= 2.5: over25 += 1
                resultados.append('G' if g_h > g_a else 'E' if g_h == g_a else 'P')
            elif condicion == 'visitante' and a == equipo:
                gf.append(g_a)
                gc.append(g_h)
                if g_h > 0 and g_a > 0: btts += 1
                if (g_h + g_a) >= 2.5: over25 += 1
                resultados.append('G' if g_a > g_h else 'E' if g_a == g_h else 'P')
        except:
            continue

    total = len(gf)
    if total == 0:
        return None

    return {
        'forma': ''.join(resultados[-5:]),
        'gf': round(statistics.mean(gf), 2),
        'gc': round(statistics.mean(gc), 2),
        'btts_pct': round(btts / total * 100, 1),
        'over25_pct': round(over25 / total * 100, 1)
    }

# Generar justificación basada en datos
def generar_justificacion(home, stats_home, stats_away):
    frases = []

    if stats_home['gf'] >= 1.8:
        frases += [
            f"{home} está mostrando un poder ofensivo notable como local.",
            f"{home} promedia más de 1.8 goles por juego en casa, lo que lo convierte en un rival temible.",
            f"La línea ofensiva de {home} ha sido consistente y peligrosa en su estadio."
        ]

    if stats_away['gc'] >= 1.6:
        frases += [
            "El visitante ha mostrado debilidades defensivas en sus salidas recientes.",
            "La defensa del visitante ha recibido demasiados goles lejos de casa.",
            "El equipo visitante sufre en defensa cuando juega fuera de su estadio."
        ]

    if stats_home['forma'].count('G') >= 3:
        frases += [
            f"{home} viene en buena racha como local, ganando la mayoría de sus últimos partidos.",
            f"La racha positiva en casa es un respaldo sólido para {home}.",
            f"{home} ha convertido su estadio en una fortaleza en los últimos encuentros."
        ]

    if stats_home['btts_pct'] >= 65 or stats_away['btts_pct'] >= 65:
        frases += [
            "La tendencia de ambos equipos indica alta probabilidad de que ambos marquen.",
            "El mercado de BTTS cobra sentido con estos equipos por su estilo abierto.",
            "Ambos equipos suelen involucrarse en partidos con goles en ambas porterías."
        ]

    if stats_home['over25_pct'] >= 65 and stats_away['over25_pct'] >= 65:
        frases += [
            "El promedio de goles en sus encuentros sugiere un partido de más de 2.5 goles.",
            "La línea de Over 2.5 tiene valor considerando el rendimiento ofensivo de ambos.",
            "Ambos conjuntos superan el 65% de Over 2.5 en sus juegos recientes."
        ]

    if stats_home['gc'] <= 1.0 and stats_away['gf'] <= 1.0:
        frases += [
            "Ambos equipos han mostrado solidez defensiva, lo que sugiere un duelo cerrado.",
            "Pocos goles encajados por el local y escasa producción ofensiva del visitante podrían frenar el ritmo del partido."
        ]

    if stats_home['gf'] >= 1.5 and stats_home['forma'].count('P') == 0:
        frases += [
            f"{home} ha evitado derrotas y mantiene su eficacia ofensiva en casa.",
            f"El rendimiento de {home} sin derrotas recientes y con goles lo hacen destacar."
        ]

    if stats_away['forma'].count('P') >= 3:
        frases += [
            "El visitante acumula varias derrotas recientes, lo que lo hace vulnerable.",
            "La forma actual del visitante deja dudas sobre su competitividad."
        ]

    if not frases:
        return "Valor detectado según forma y cuota disponible."

    return random.choice(frases)

# Obtener partidos del día
hoy = datetime.datetime.now().strftime("%Y-%m-%d")
res = requests.get(f"{API_URL}/fixtures?date={hoy}", headers=HEADERS)
fixtures_raw = res.json().get("response", [])
fixtures = []
for f in fixtures_raw:
    fecha_fixture = f['fixture']['date'][:10]
    status_fixture = f['fixture']['status']['short']
    if status_fixture in ['NS', 'TBD'] and fecha_fixture == hoy:
        fixtures.append(f)

if not fixtures:
    print("📭 No hay partidos disponibles hoy con status 'NS' o 'TBD'.")

for partido in fixtures:
    lname = partido['league']['name']
    liga_clave = re.sub(r"[^a-z0-9_]", "_", lname.lower().replace(" ", "_"))
    print(f"🔍 Liga detectada: {liga_clave}")
    if liga_clave not in historial:
        print(f"⚠️ Liga {liga_clave} no está en el historial. Se omite.")
        continue
    try:
        lname = partido['league']['name']
        liga_clave = re.sub(r"[^a-z0-9_]", "_", lname.lower().replace(" ", "_"))
        print(f"🔍 Liga detectada: {liga_clave}")
        if liga_clave not in historial:
            print(f"⚠️ Liga {liga_clave} no está en el historial. Se omite.")
            continue
        print(f"❌ Error en análisis del fixture: {e}")

