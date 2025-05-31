import requests
import os
from datetime import datetime
import pytz
import statistics
from dateutil import parser
import logging
import csv
import sys
import time
from colorama import init, Fore, Style

# Inicializar colorama
init()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Validar API key
API_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_KEY:
    logging.error("API_FOOTBALL_KEY no está configurada.")
    print(Fore.RED + "❌ Error: API_FOOTBALL_KEY no está configurada." + Style.RESET_ALL)
    sys.exit(1)

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
REQUEST_TIMEOUT = 10  # Timeout de 10 segundos para todas las solicitudes

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_partidos_hoy():
    hoy = datetime.now(pytz.utc).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    try:
        logging.info(f"Iniciando solicitud para obtener partidos de la fecha {hoy}")
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Respuesta recibida: {len(data.get('response', []))} partidos encontrados")
        partidos_validos = []
        for fixture in data.get("response", []):  # Eliminar límite [:3], procesar todos
            if fixture["league"]["id"] in LIGAS_VALIDAS:
                if fixture["fixture"]["status"]["short"] != "NS":
                    continue
                partidos_validos.append({
                    "liga": fixture["league"]["name"],
                    "local": fixture["teams"]["home"]["name"],
                    "visitante": fixture["teams"]["away"]["name"],
                    "hora_utc": fixture["fixture"]["date"],
                    "id_fixture": fixture["fixture"]["id"],
                    "home_id": fixture["teams"]["home"]["id"],
                    "away_id": fixture["teams"]["away"]["id"]
                })
        logging.info(f"Se encontraron {len(partidos_validos)} partidos válidos.")
        return partidos_validos
    except requests.Timeout:
        logging.error("Tiempo de espera agotado al obtener partidos.")
        print(Fore.RED + "❌ Error: Tiempo de espera agotado al obtener partidos." + Style.RESET_ALL)
        return []
    except requests.RequestException as e:
        logging.error(f"Error al obtener partidos: {e}")
        print(Fore.RED + f"❌ Error al obtener partidos: {e}" + Style.RESET_ALL)
        return []

def obtener_cuotas_por_mercado(fixture_id, bet_id):
    try:
        url = f"{BASE_URL}/odds?fixture={fixture_id}&bet={bet_id}"
        logging.info(f"Iniciando solicitud de cuotas para fixture {fixture_id}, bet {bet_id}")
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if data.get("response") and data["response"][0].get("bookmakers"):
            logging.info(f"Cuotas obtenidas para fixture {fixture_id}, bet {bet_id}")
            return data["response"][0]["bookmakers"][0]["bets"][0]["values"]
        logging.warning(f"Sin datos de cuotas para fixture {fixture_id}, bet {bet_id}")
        return []
    except requests.Timeout:
        logging.error("Tiempo de espera agotado al obtener cuotas.")
        return []
    except (requests.RequestException, KeyError, IndexError) as e:
        logging.error(f"Error al obtener cuotas: {e}")
        return []

def convertir_horas(hora_utc_str):
    try:
        hora_utc = parser.isoparse(hora_utc_str)
        return (
            hora_utc.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M"),
            hora_utc.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
        )
    except ValueError as e:
        logging.error(f"Error al parsear fecha {hora_utc_str}: {e}")
        return "N/A", "N/A"

def obtener_estadisticas_equipo(equipo_id, condicion):
    url = f"{BASE_URL}/fixtures?team={equipo_id}&last=20"
    try:
        logging.info(f"Iniciando solicitud de estadísticas para equipo {equipo_id}, condición {condicion}")
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        gf, gc, tiros, posesion, tarjetas_amarillas, corners = [], [], [], [], [], []
        ganados = empatados = perdidos = 0

        for match in data.get("response", [])[:5]:
            if condicion == "local" and match["teams"]["home"]["id"] != equipo_id:
                continue
            if condicion == "visitante" and match["teams"]["away"]["id"] != equipo_id:
                continue

            try:
                fixture_id = match["fixture"]["id"]
                if match["teams"]["home"]["id"] == equipo_id:
                    goles_favor = match["goals"]["home"]
                    goles_contra = match["goals"]["away"]
                else:
                    goles_favor = match["goals"]["away"]
                    goles_contra = match["goals"]["home"]

                if isinstance(goles_favor, (int, float)) and isinstance(goles_contra, (int, float)):
                    gf.append(goles_favor)
                    gc.append(goles_contra)

                    if goles_favor > goles_contra:
                        ganados += 1
                    elif goles_favor == goles_contra:
                        empatados += 1
                    else:
                        perdidos += 1

                stats_url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}&team={equipo_id}"
                logging.info(f"Solicitando estadísticas para fixture {fixture_id}, equipo {equipo_id}")
                stats_res = requests.get(stats_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                stats_res.raise_for_status()
                stats_data = stats_res.json()
                if not stats_data.get("response"):
                    continue

                stats = stats_data["response"][0].get("statistics", [])
                for stat in stats:
                    if stat["type"] == "Shots on Goal" and isinstance(stat["value"], (int, float)):
                        tiros.append(int(stat["value"]))
                    if stat["type"] == "Ball Possession" and stat["value"]:
                        try:
                            posesion.append(int(stat["value"].replace("%", "")))
                        except (ValueError, TypeError):
                            continue
                    if stat["type"] == "Yellow Cards" and isinstance(stat["value"], (int, float)):
                        tarjetas_amarillas.append(int(stat["value"]))
                    if stat["type"] == "Corners" and isinstance(stat["value"], (int, float)):
                        corners.append(int(stat["value"]))
            except (requests.Timeout, requests.RequestException, KeyError, TypeError):
                continue

        stats = {
            "gf": round(statistics.mean(gf), 2) if gf else 0,
            "gc": round(statistics.mean(gc), 2) if gc else 0,
            "tiros": round(statistics.mean(tiros), 1) if tiros else "N/A",
            "posesion": round(statistics.mean(posesion), 1) if posesion else "N/A",
            "tarjetas_amarillas": round(statistics.mean(tarjetas_amarillas), 1) if tarjetas_amarillas else "N/A",
            "corners": round(statistics.mean(corners), 1) if corners else "N/A",
            "forma": f"{ganados}G - {empatados}E - {perdidos}P"
        }
        logging.info(f"Estadísticas obtenidas: {stats}")
        return stats
    except requests.Timeout:
        logging.error("Tiempo de espera agotado al obtener estadísticas.")
        return {"gf": 0, "gc": 0, "tiros": "N/A", "posesion": "N/A", "tarjetas_amarillas": "N/A", "corners": "N/A", "forma": "0G - 0E - 0P"}
    except requests.RequestException as e:
        logging.error(f"Error al obtener estadísticas: {e}")
        return {"gf": 0, "gc": 0, "tiros": "N/A", "posesion": "N/A", "tarjetas_amarillas": "N/A", "corners": "N/A", "forma": "0G - 0E - 0P"}

def predecir_marcador(local, visitante):
    g_local = round((local["gf"] + visitante["gc"]) / 2 * 1.1)
    g_visit = round((visitante["gf"] + local["gc"]) / 2 * 0.9)
    return g_local, g_visit

def elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts):
    if not cuotas_ml or len(cuotas_ml) < 3:
        if goles_local + goles_away >= 3 and cuota_over != "❌":
            return f"🎯 Pick sugerido: Over 2.5 goles @ {cuota_over}"
        elif goles_local >= 1 and goles_away >= 1 and cuota_btts != "❌":
            return f"🎯 Pick sugerido: Ambos anotan (BTTS) @ {cuota_btts}"
        return "🎯 Pick sugerido: ❌ Sin valor claro en el mercado"
    if goles_local > goles_away:
        return f"🎯 Pick sugerido: Gana {p['local']} @ {cuotas_ml[0]['odd']}"
    elif goles_local < goles_away:
        return f"🎯 Pick sugerido: Gana {p['visitante']} @ {cuotas_ml[2]['odd']}"
    elif goles_local == goles_away:
        return f"🎯 Pick sugerido: Empate @ {cuotas_ml[1]['odd']}"
    elif goles_local + goles_away >= 3 and cuota_over != "❌":
        return f"🎯 Pick sugerido: Over 2.5 goles @ {cuota_over}"
    elif goles_local >= 1 and goles_away >= 1 and cuota_btts != "❌":
        return f"🎯 Pick sugerido: Ambos anotan (BTTS) @ {cuota_btts}"
    return "🎯 Pick sugerido: ❌ Sin valor claro en el mercado"

def evaluar_advertencia(pick, stats_local, stats_away):
    advertencia = ""
    if "Gana" in pick and "Empate" not in pick:
        equipo = pick.split("Gana ")[1].split(" @")[0]
        if equipo in stats_local.get("nombre", ""):
            victorias = int(stats_local["forma"].split("G")[0])
            if victorias < 2:
                advertencia = "⚠️ Ojo: el equipo local no viene en buena forma."
        elif equipo in stats_away.get("nombre", ""):
            victorias = int(stats_away["forma"].split("G")[0])
            if victorias < 2:
                advertencia = "⚠️ Cuidado: el visitante no viene fuerte."
    return advertencia

def calcular_score(stats_local, stats_away, goles_local, goles_away, cuota):
    score = 0
    if abs(goles_local - goles_away) >= 2:
        score += 2
    if stats_local["forma"].startswith(("3", "4", "5")):
        score += 1
    if isinstance(stats_local["tiros"], (int, float)) and stats_local["tiros"] >= 4:
        score += 1
    if isinstance(stats_local["posesion"], (int, float)) and stats_local["posesion"] >= 55:
        score += 1
    try:
        cuota_valor = float(cuota)
        if 1.55 <= cuota_valor <= 3.50:
            score += 1
    except (ValueError, TypeError):
        pass
    return score

def interpretar_score(score):
    if score >= 5:
        return f"💎 PICK DESTACADO (Score: {score}/6)"
    elif score == 4:
        return f"✅ PICK CON VALOR (Score: {score}/6)"
    elif score <= 2:
        return f"⚠️ PICK DUDOSO (Score: {score}/6)"
    return f"Score: {score}/6"

def calcular_probabilidades_btts_over(equipo_id, condicion):
    try:
        url = f"{BASE_URL}/fixtures?team={equipo_id}&last=20"
        logging.info(f"Iniciando solicitud para calcular probabilidades BTTS/Over para equipo {equipo_id}")
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        btts_count = 0
        over25_count = 0
        total_partidos = 0

        for match in data.get("response", [])[:5]:
            if condicion == "local" and match["teams"]["home"]["id"] != equipo_id:
                continue
            if condicion == "visitante" and match["teams"]["away"]["id"] != equipo_id:
                continue

            goles_local = match["goals"]["home"]
            goles_visitante = match["goals"]["away"]

            if not isinstance(goles_local, (int, float)) or not isinstance(goles_visitante, (int, float)):
                continue

            total_partidos += 1
            if goles_local + goles_visitante >= 3:
                over25_count += 1
            if goles_local > 0 and goles_visitante > 0:
                btts_count += 1

        if total_partidos == 0:
            return {"btts": 0, "over": 0}
        probs = {
            "btts": round((btts_count / total_partidos) * 100),
            "over": round((over25_count / total_partidos) * 100)
        }
        logging.info(f"Probabilidades calculadas: {probs}")
        return probs
    except requests.Timeout:
        logging.error("Tiempo de espera agotado al calcular probabilidades.")
        return {"btts": 0, "over": 0}
    except requests.RequestException as e:
        logging.error(f"Error al calcular probabilidades: {e}")
        return {"btts": 0, "over": 0}

if __name__ == "__main__":
    try:
        logging.info("Iniciando script")
        output_file = f"picks_{datetime.now().strftime('%Y%m%d')}.csv"
        logging.info(f"Creando archivo de salida: {output_file}")
        picks_valiosos = []

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Liga', 'Partido', 'Hora MX', 'Hora ES', 'Cuotas', 'Over 2.5', 'BTTS', 'BTTS Predicho', 'Stats Local', 'Stats Visitante', 'Predicción', 'Pick', 'Advertencia', 'Score'])

            partidos = obtener_partidos_hoy()
            if not partidos:
                logging.warning("No se encontraron partidos válidos.")
                print("⚠️ No hay partidos válidos.")
                sys.exit(0)

            for p in partidos:
                logging.info(f"Procesando partido: {p['local']} vs {p['visitante']}")
                cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)
                cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)
                cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)

                cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
                cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

                hora_mex, hora_esp = convertir_horas(p["hora_utc"])

                stats_local = obtener_estadisticas_equipo(p["home_id"], "local")
                stats_away = obtener_estadisticas_equipo(p["away_id"], "visitante")
                stats_local["nombre"] = p["local"]
                stats_away["nombre"] = p["visitante"]

                goles_local, goles_away = predecir_marcador(stats_local, stats_away)
                btts_pred = "Sí" if goles_local >= 1 and goles_away >= 1 else "No"

                pick = elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts)
                cuota_principal = pick.split("@")[-1].strip() if "@" in pick else "0"
                score = calcular_score(stats_local, stats_away, goles_local, goles_away, cuota_principal)

                if score < 4:
                    logging.info(f"Partido descartado (score: {score})")
                    continue

                pick_display = f"{pick} ⭐" if score >= 4 and "❌" not in pick else pick

                print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]}')
                print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')
                print(f'Cuotas: 🏠 {cuotas_ml[0]["odd"] if cuotas_ml and len(cuotas_ml) > 0 else "❌"} | '
                      f'🤝 {cuotas_ml[1]["odd"] if cuotas_ml and len(cuotas_ml) > 1 else "❌"} | '
                      f'🛫 {cuotas_ml[2]["odd"] if cuotas_ml and len(cuotas_ml) > 2 else "❌"}')
                print(f'Over 2.5: {cuota_over} | BTTS: {cuota_btts} | BTTS Predicho: {btts_pred}')
                print(f'📊 {p["local"]} (Local): GF {stats_local["gf"]} | GC {stats_local["gc"]} | '
                      f'Tiros {stats_local["tiros"]} | Posesión {stats_local["posesion"]}% | '
                      f'Tarjetas Amarillas {stats_local["tarjetas_amarillas"]} | Corners {stats_local["corners"]} | '
                      f'Forma: {stats_local["forma"]}')
                print(f'📊 {p["visitante"]} (Visitante): GF {stats_away["gf"]} | GC {stats_away["gc"]} | '
                      f'Tiros {stats_away["tiros"]} | Posesión {stats_away["posesion"]}% | '
                      f'Tarjetas Amarillas {stats_away["tarjetas_amarillas"]} | Corners {stats_away["corners"]} | '
                      f'Forma: {stats_away["forma"]}')
                print(f'🔮 Predicción: {p["local"]} {goles_local} - {goles_away} {p["visitante"]}')
                print(Fore.GREEN + pick_display + Style.RESET_ALL if score >= 4 and "❌" not in pick_display else pick_display)
                advertencia = evaluar_advertencia(pick, stats_local, stats_away)
                if advertencia:
                    print(Fore.RED + advertencia + Style.RESET_ALL)
                print(interpretar_score(score))

                prob_local = calcular_probabilidades_btts_over(p["home_id"], "local")
                prob_away = calcular_probabilidades_btts_over(p["away_id"], "visitante")
                print(f'📊 Probabilidades:')
                print(f'- {p["local"]}: BTTS {prob_local["btts"]}% | Over 2.5 {prob_local["over"]}%')
                print(f'- {p["visitante"]}: BTTS {prob_away["btts"]}% | Over 2.5 {prob_away["over"]}%')
                print("-" * 60)

                writer.writerow([
                    p["liga"],
                    f"{p['local']} vs {p['visitante']}",
                    hora_mex,
                    hora_esp,
                    f"🏠 {cuotas_ml[0]['odd'] if cuotas_ml and len(cuotas_ml) > 0 else '❌'} | 🤝 {cuotas_ml[1]['odd'] if cuotas_ml and len(cuotas_ml) > 1 else '❌'} | 🛫 {cuotas_ml[2]['odd'] if cuotas_ml and len(cuotas_ml) > 2 else '❌'}",
                    cuota_over,
                    cuota_btts,
                    btts_pred,
                    f"GF {stats_local['gf']} | GC {stats_local['gc']} | Tiros {stats_local['tiros']} | Posesión {stats_local['posesion']}% | Tarjetas Amarillas {stats_local['tarjetas_amarillas']} | Corners {stats_local['corners']} | Forma: {stats_local['forma']}",
                    f"GF {stats_away['gf']} | GC {stats_away['gc']} | Tiros {stats_away['tiros']} | Posesión {stats_away['posesion']}% | Tarjetas Amarillas {stats_away['tarjetas_amarillas']} | Corners {stats_away['corners']} | Forma: {stats_away['forma']}",
                    f"{p['local']} {goles_local} - {goles_away} {p['visitante']}",
                    pick_display,
                    advertencia,
                    interpretar_score(score)
                ])

                picks_valiosos.append({
                    "partido": f"{p['local']} vs {p['visitante']}",
                    "liga": p["liga"],
                    "pick": pick_display,
                    "score": interpretar_score(score)
                })
                time.sleep(1)  # Pausa de 1 segundo entre partidos

        if picks_valiosos:
            logging.info("Resumen de Picks Valiosos (Score >= 4):")
            print("\n📊 Resumen de Picks Valiosos (Score >= 4):")
            for pick in picks_valiosos:
                print(f"{pick['liga']}: {pick['partido']} - {pick['pick']} ({pick['score']})")
        else:
            logging.info("No se encontraron picks valiosos.")
            print("⚠️ No se encontraron picks valiosos.")

        logging.info("Script finalizado.")
        print("✅ Script finalizado.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        print(Fore.RED + f"❌ Error inesperado: {e}" + Style.RESET_ALL)
        sys.exit(1)
