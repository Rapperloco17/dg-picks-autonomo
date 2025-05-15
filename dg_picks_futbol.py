import os
import json
import datetime
import requests
import re
import glob
import statistics

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

# Extrae forma y promedio de goles, corners, tarjetas
def calcular_stats_equipo(juegos, equipo, condicion):
    gf, gc, btts, over25, corners, corners_concedidos, tarjetas = [], [], 0, 0, [], [], []
    resultados = []
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
                stats = partido.get('statistics', {})
                corners.append(stats.get('home_corners', 0))
                corners_concedidos.append(stats.get('away_corners', 0))
                tarjetas.append(stats.get('home_cards', 0))
            elif condicion == 'visitante' and a == equipo:
                gf.append(g_a)
                gc.append(g_h)
                if g_h > 0 and g_a > 0: btts += 1
                if (g_h + g_a) >= 2.5: over25 += 1
                resultados.append('G' if g_a > g_h else 'E' if g_a == g_h else 'P')
                stats = partido.get('statistics', {})
                corners.append(stats.get('away_corners', 0))
                corners_concedidos.append(stats.get('home_corners', 0))
                tarjetas.append(stats.get('away_cards', 0))
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
        'over25_pct': round(over25 / total * 100, 1),
        'corners': round(statistics.mean(corners), 2) if corners else 0,
        'concedidos': round(statistics.mean(corners_concedidos), 2) if corners_concedidos else 0,
        'tarjetas': round(statistics.mean(tarjetas), 2) if tarjetas else 0
    }

# Obtener partidos del día
hoy = datetime.datetime.now().strftime("%Y-%m-%d")
res = requests.get(f"{API_URL}/fixtures?date={hoy}", headers=HEADERS)
fixtures = res.json().get("response", [])

for partido in fixtures:
    try:
        lid = partido['league']['id']
        lname = partido['league']['name']
        fixture_id = partido['fixture']['id']
        home = partido['teams']['home']['name']
        away = partido['teams']['away']['name']

        liga_clave = re.sub(r"[^a-z0-9_]", "_", lname.lower().replace(" ", "_"))
        if liga_clave not in historial:
            continue

        historial_liga = historial[liga_clave]
        stats_home = calcular_stats_equipo(historial_liga, home, 'local')
        stats_away = calcular_stats_equipo(historial_liga, away, 'visitante')
        if not stats_home or not stats_away:
            continue

        # Obtener cuota ML local desde API
        odds_url = f"{API_URL}/odds?fixture={fixture_id}&bookmaker=1"
        odds_res = requests.get(odds_url, headers=HEADERS).json()
        cuota = None
        for bk in odds_res.get('response', []):
            markets = bk.get('bookmakers', [])
            for m in markets:
                for bet in m.get('bets', []):
                    if bet['name'] == 'Match Winner':
                        for v in bet['values']:
                            if v['value'] == 'Home':
                                cuota = v['odd']
        
        # Pick sugerido
        pick = f"Gana {home}" if stats_home['gf'] >= 1.5 and stats_away['gc'] >= 1.5 else None
        if pick:
            mensaje = f"\n⚽ *{home} vs {away}* ({lname})\n"
            mensaje += f"\n✅ *Pick sugerido:* {pick}"
            if cuota:
                mensaje += f"\n💰 Cuota: @ {cuota}"
            mensaje += f"\n\n📊 Forma {home}: {stats_home['forma']} | Prom. {stats_home['gf']} GF / {stats_home['gc']} GC"
            mensaje += f"\n📊 Forma {away}: {stats_away['forma']} | Prom. {stats_away['gf']} GF / {stats_away['gc']} GC"
            mensaje += f"\n\n📉 Córners: {stats_home['corners']} / {stats_away['corners']}"
            mensaje += f"\n📉 Córners concedidos: {stats_home['concedidos']} / {stats_away['concedidos']}"
            mensaje += f"\n🟨 Tarjetas: {stats_home['tarjetas']} / {stats_away['tarjetas']}"
            mensaje += f"\n\n🧠 Justificación: Local fuerte en casa, buena forma, visitante concede."
            mensaje += f"\n✅ Valor detectado en la cuota"
            print(mensaje)
    except Exception as e:
        print(f"❌ Error en análisis del fixture: {e}")

