import requests
import os
from datetime import datetime, timedelta
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

# Configurar logging para depuración (guardar en archivo, no en consola)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s',
    handlers=[logging.FileHandler("debug.log")]
)

# Validar API key
API_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_KEY:
    print(Fore.RED + "❌ Error: API_FOOTBALL_KEY no está configurada." + Style.RESET_ALL)
    sys.exit(1)

# Rango de fechas (hoy y mañana)
TODAY = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
TOMORROW = (datetime.now(pytz.timezone("America/Mexico_City")) + timedelta(days=1)).strftime("%Y-%m-%d")
DATE_RANGE = [TODAY, TOMORROW]
SEASON = "2025"

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
REQUEST_TIMEOUT = 10

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

# Datos simulados para pruebas
SIMULATED_FIXTURES = [
    {
        "liga": "Chile Primera Division",
        "local": "Universidad de Chile",
        "visitante": "O'Higgins",
        "hora_utc": "2025-05-31T23:00:00+00:00",
        "id_fixture": 9999,
        "home_id": 1001,
        "away_id": 1002,
        "goles_local": None,
        "goles_visitante": None
    }
]

def obtener_partidos_rango_fechas(use_simulated=False):
    if use_simulated:
        logging.debug("Usando datos simulados para partidos.")
        return SIMULATED_FIXTURES

    partidos_validos = []
    for date in DATE_RANGE:
        for league_id in LIGAS_VALIDAS:
            url = f"{BASE_URL}/fixtures?league={league_id}&date={date}&season={SEASON}"
            try:
                logging.debug(f"Solicitando partidos para liga {league_id} en {date}")
                response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                partidos = data.get('response', [])
                logging.debug(f"Encontrados {len(partidos)} partidos para liga {league_id} en {date}")
                for fixture in partidos:
                    partidos_validos.append({
                        "liga": fixture["league"]["name"],
                        "local": fixture["teams"]["home"]["name"],
                        "visitante": fixture["teams"]["away"]["name"],
                        "hora_utc": fixture["fixture"]["date"],
                        "id_fixture": fixture["fixture"]["id"],
                        "home_id": fixture["teams"]["home"]["id"],
                        "away_id": fixture["teams"]["away"]["id"],
                        "goles_local": fixture["goals"]["home"] if fixture["goals"]["home"] is not None else None,
                        "goles_visitante": fixture["goals"]["away"] if fixture["goals"]["away"] is not None else None
                    })
            except requests.Timeout:
                logging.warning(f"Tiempo de espera agotado para liga {league_id} en {date}")
                continue
            except requests.RequestException as e:
                logging.error(f"Error al obtener partidos para liga {league_id} en {date}: {e}")
                continue
    
    partidos_validos.sort(key=lambda x: parser.isoparse(x["hora_utc"]))
    logging.debug(f"Total partidos válidos: {len(partidos_validos)}")
    return partidos_validos

def obtener_cuotas_por_mercado(fixture_id, bet_id, use_simulated=False):
    if use_simulated:
        if bet_id == 1:  # Moneyline
            return [{"value": "Home", "odd": "2.10"}, {"value": "Draw", "odd": "3.20"}, {"value": "Away", "odd": "3.50"}]
        elif bet_id == 5:  # Over/Under 2.5
            return [{"value": "Over 2.5", "odd": "1.90"}, {"value": "Under 2.5", "odd": "1.80"}]
        elif bet_id == 10:  # BTTS
            return [{"value": "Yes", "odd": "1.75"}, {"value": "No", "odd": "2.00"}]
        elif bet_id == 23:  # Tarjetas
            return [{"value": "Over 4.5", "odd": "2.20"}]
        return []

    try:
        url = f"{BASE_URL}/odds?fixture={fixture_id}&bet={bet_id}"
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if data.get("response") and data["response"][0].get("bookmakers"):
            return data["response"][0]["bookmakers"][0]["bets"][0]["values"]
        return []
    except requests.Timeout:
        return []
    except (requests.RequestException, KeyError, IndexError):
        return []

def convertir_horas(hora_utc_str):
    try:
        hora_utc = parser.isoparse(hora_utc_str)
        return (
            hora_utc.astimezone(pytz.timezone("America/Mexico_City")).strftime("%H:%M"),
            hora_utc.astimezone(pytz.timezone("Europe/Madrid")).strftime("%H:%M")
        )
    except ValueError:
        return "N/A", "N/A"

def obtener_h2h(home_id, away_id, use_simulated=False):
    if use_simulated:
        return {
            "record": "2G (local) - 1E - 2G (visitante)",
            "home_avg_goals": 1.2,
            "away_avg_goals": 1.0,
            "btts_percentage": 60,
            "total_matches": 5,
            "home_dominance": False,
            "away_dominance": False,
            "avg_yellow_cards": 2.5,
            "avg_red_cards": 1.0,
            "avg_total_cards": 3.5,
            "intense_rivalry": False
        }

    url = f"{BASE_URL}/fixtures/head2head?team1={home_id}&team2={away_id}&last=5"
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals = []
        away_goals = []
        btts_count = 0
        total_matches = 0
        total_yellow_cards = []
        total_red_cards = []
        has_red_cards = False

        if not data.get("response"):
            return {
                "record": "N/A", "home_avg_goals": 0, "away_avg_goals": 0, "btts_percentage": 0,
                "total_matches": 0, "home_dominance": False, "away_dominance": False,
                "avg_yellow_cards": 0, "avg_red_cards": 0, "avg_total_cards": 0, "intense_rivalry": False
            }

        for match in data.get("response", [])[:5]:
            goles_local = match["goals"]["home"]
            goles_visitante = match["goals"]["away"]
            home_team_id = match["teams"]["home"]["id"]
            fixture_id = match["fixture"]["id"]

            if not isinstance(goles_local, (int, float)) or not isinstance(goles_visitante, (int, float)):
                continue

            total_matches += 1
            if home_team_id == home_id:
                home_goals.append(goles_local)
                away_goals.append(goles_visitante)
                if goles_local > goles_visitante:
                    home_wins += 1
                elif goles_local < goles_visitante:
                    away_wins += 1
                else:
                    draws += 1
            else:
                home_goals.append(goles_visitante)
                away_goals.append(goles_local)
                if goles_visitante > goles_local:
                    home_wins += 1
                elif goles_visitante < goles_local:
                    away_wins += 1
                else:
                    draws += 1

            if goles_local > 0 and goles_visitante > 0:
                btts_count += 1

            stats_url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
            try:
                stats_res = requests.get(stats_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                stats_res.raise_for_status()
                stats_data = stats_res.json()
                if stats_data.get("response"):
                    total_team_cards = 0
                    for team_stats in stats_data["response"]:
                        yellow_cards = 0
                        red_cards = 0
                        for stat in team_stats.get("statistics", []):
                            if stat["type"] == "Yellow Cards" and isinstance(stat["value"], (int, float)):
                                yellow_cards = int(stat["value"])
                            if stat["type"] == "Red Cards" and isinstance(stat["value"], (int, float)):
                                red_cards = int(stat["value"])
                        total_team_cards += yellow_cards + red_cards
                    total_yellow_cards.append(yellow_cards)
                    total_red_cards.append(red_cards)
                    if red_cards > 0:
                        has_red_cards = True
            except (requests.Timeout, requests.RequestException, KeyError, TypeError):
                continue

        avg_yellow_cards = round(statistics.mean(total_yellow_cards), 1) if total_yellow_cards else 0
        avg_red_cards = round(statistics.mean(total_red_cards), 1) if total_red_cards else 0
        avg_total_cards = avg_yellow_cards + avg_red_cards
        intense_rivalry = (avg_total_cards >= 4.5) or has_red_cards

        return {
            "record": f"{home_wins}G (local) - {draws}E - {away_wins}G (visitante)",
            "home_avg_goals": round(statistics.mean(home_goals), 2) if home_goals else 0,
            "away_avg_goals": round(statistics.mean(away_goals), 2) if away_goals else 0,
            "btts_percentage": round((btts_count / total_matches) * 100) if total_matches > 0 else 0,
            "total_matches": total_matches,
            "home_dominance": home_wins > (total_matches / 2) if total_matches > 0 else False,
            "away_dominance": away_wins > (total_matches / 2) if total_matches > 0 else False,
            "avg_yellow_cards": avg_yellow_cards,
            "avg_red_cards": avg_red_cards,
            "avg_total_cards": avg_total_cards,
            "intense_rivalry": intense_rivalry
        }
    except requests.Timeout:
        return {
            "record": "N/A", "home_avg_goals": 0, "away_avg_goals": 0, "btts_percentage": 0,
            "total_matches": 0, "home_dominance": False, "away_dominance": False,
            "avg_yellow_cards": 0, "avg_red_cards": 0, "avg_total_cards": 0, "intense_rivalry": False
        }
    except requests.RequestException:
        return {
            "record": "N/A", "home_avg_goals": 0, "away_avg_goals": 0, "btts_percentage": 0,
            "total_matches": 0, "home_dominance": False, "away_dominance": False,
            "avg_yellow_cards": 0, "avg_red_cards": 0, "avg_total_cards": 0, "intense_rivalry": False
        }

def obtener_estadisticas_equipo(equipo_id, use_simulated=False):
    if use_simulated:
        return {
            "gf": 1.50 if equipo_id == 1001 else 1.10,
            "gc": 1.20 if equipo_id == 1001 else 1.40,
            "tiros": 4.0,
            "posesion": 50.0,
            "tarjetas_amarillas": 2.0 if equipo_id == 1001 else 2.2,
            "corners": 4.0 if equipo_id == 1001 else 3.8,
            "forma": "7G - 6E - 7P" if equipo_id == 1001 else "5G - 8E - 7P",
            "partidos_usados": 20
        }

    url = f"{BASE_URL}/fixtures?team={equipo_id}&last=50&season={SEASON}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        gf, gc, tiros, posesion, tarjetas_amarillas, corners = [], [], [], [], [], []
        ganados = empatados = perdidos = 0
        partidos_usados = 0

        for match in data.get("response", [])[:20]:
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
                    partidos_usados += 1

                    if goles_favor > goles_contra:
                        ganados += 1
                    elif goles_favor == goles_contra:
                        empatados += 1
                    else:
                        perdidos += 1

                stats_url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}&team={equipo_id}"
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

        if partidos_usados < 5:
            print(Fore.YELLOW + f"⚠️ Advertencia: Solo se encontraron {partidos_usados} partidos válidos para {equipo_id}. Análisis limitado." + Style.RESET_ALL)

        return {
            "gf": round(statistics.mean(gf), 2) if gf else 0,
            "gc": round(statistics.mean(gc), 2) if gc else 0,
            "tiros": round(statistics.mean(tiros), 1) if tiros else "N/A",
            "posesion": round(statistics.mean(posesion), 1) if posesion else "N/A",
            "tarjetas_amarillas": round(statistics.mean(tarjetas_amarillas), 1) if tarjetas_amarillas else "N/A",
            "corners": round(statistics.mean(corners), 1) if corners else "N/A",
            "forma": f"{ganados}G - {empatados}E - {perdidos}P",
            "partidos_usados": partidos_usados
        }
    except requests.Timeout:
        return {"gf": 0, "gc": 0, "tiros": "N/A", "posesion": "N/A", "tarjetas_amarillas": "N/A", "corners": "N/A", "forma": "0G - 0E - 0P", "partidos_usados": 0}
    except requests.RequestException:
        return {"gf": 0, "gc": 0, "tiros": "N/A", "posesion": "N/A", "tarjetas_amarillas": "N/A", "corners": "N/A", "forma": "0G - 0E - 0P", "partidos_usados": 0}

def predecir_marcador(local, visitante, h2h_stats):
    g_local = round(((local["gf"] + visitante["gc"]) / 2 * 0.7 + h2h_stats["home_avg_goals"] * 0.3) * 1.1)
    g_visit = round(((visitante["gf"] + local["gc"]) / 2 * 0.7 + h2h_stats["away_avg_goals"] * 0.3) * 0.9)
    return g_local, g_visit

def elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts, h2h_stats, stats_local, stats_away, use_simulated=False):
    cuotas_cards = obtener_cuotas_por_mercado(p["id_fixture"], 23, use_simulated)
    cuota_over_cards = next((x["odd"] for x in cuotas_cards if "Over 4.5" in x["value"]), "❌")

    intense_rivalry = h2h_stats["intense_rivalry"]
    if h2h_stats["total_matches"] == 0 and isinstance(stats_local["tarjetas_amarillas"], (int, float)) and isinstance(stats_away["tarjetas_amarillas"], (int, float)):
        avg_cards = (stats_local["tarjetas_amarillas"] + stats_away["tarjetas_amarillas"]) / 2
        intense_rivalry = avg_cards >= 2.5

    if intense_rivalry and cuota_over_cards != "❌":
        return f"🎯 Pick sugerido: Over 4.5 tarjetas @ {cuota_over_cards} (Rivalidad intensa detectada)"

    if not cuotas_ml or len(cuotas_ml) < 3:
        if goles_local + goles_away >= 3 and cuota_over != "❌":
            return f"🎯 Pick sugerido: Over 2.5 goles @ {cuota_over}"
        elif goles_local >= 1 and goles_away >= 1 and cuota_btts != "❌":
            return f"🎯 Pick sugerido: Ambos anotan (BTTS) @ {cuota_btts}"
        return "🎯 Pick sugerido: ❌ Sin valor claro en el mercado"

    if h2h_stats["home_dominance"] and goles_local >= goles_away:
        return f"🎯 Pick sugerido: Gana {p['local']} @ {cuotas_ml[0]['odd']} (H2H favorece)"
    elif h2h_stats["away_dominance"] and goles_away >= goles_local:
        return f"🎯 Pick sugerido: Gana {p['visitante']} @ {cuotas_ml[2]['odd']} (H2H favorece)"
    elif goles_local > goles_away:
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

def evaluar_advertencia(pick, stats_local, stats_away, h2h_stats):
    advertencia = ""
    if "Gana" in pick and "Empate" not in pick:
        equipo = pick.split("Gana ")[1].split(" @")[0]
        if equipo in stats_local.get("nombre", ""):
            victorias = int(stats_local["forma"].split("G")[0])
            if victorias < 7:
                advertencia = "⚠️ Ojo: el equipo local no viene en buena forma."
        elif equipo in stats_away.get("nombre", ""):
            victorias = int(stats_away["forma"].split("G")[0])
            if victorias < 7:
                advertencia = "⚠️ Cuidado: el visitante no viene fuerte."
    intense_rivalry = h2h_stats["intense_rivalry"]
    if h2h_stats["total_matches"] == 0 and isinstance(stats_local["tarjetas_amarillas"], (int, float)) and isinstance(stats_away["tarjetas_amarillas"], (int, float)):
        avg_cards = (stats_local["tarjetas_amarillas"] + stats_away["tarjetas_amarillas"]) / 2
        intense_rivalry = avg_cards >= 2.5
    if intense_rivalry and "tarjetas" not in pick.lower():
        advertencia += " ⚠️ Nota: Rivalidad intensa detectada, considera apuesta de tarjetas."
    return advertencia

def calcular_score(stats_local, stats_away, goles_local, goles_away, cuota, h2h_stats, pick):
    score = 0
    if abs(goles_local - goles_away) >= 2:
        score += 2
    if stats_local["forma"].startswith(("10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20")):
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
    if (h2h_stats["home_dominance"] and goles_local > goles_away) or (h2h_stats["away_dominance"] and goles_away > goles_local):
        score += 1
    intense_rivalry = h2h_stats["intense_rivalry"]
    if h2h_stats["total_matches"] == 0 and isinstance(stats_local["tarjetas_amarillas"], (int, float)) and isinstance(stats_away["tarjetas_amarillas"], (int, float)):
        avg_cards = (stats_local["tarjetas_amarillas"] + stats_away["tarjetas_amarillas"]) / 2
        intense_rivalry = avg_cards >= 2.5
    if intense_rivalry and "tarjetas" in pick.lower():
        score += 1
    return score

def interpretar_score(score):
    if score >= 5:
        return f"💎 PICK DESTACADO (Score: {score}/8)"
    elif score == 4:
        return f"✅ PICK CON VALOR (Score: {score}/8)"
    elif score <= 2:
        return f"⚠️ PICK DUDOSO (Score: {score}/8)"
    return f"Score: {score}/8"

def calcular_probabilidades_btts_over(equipo_id, use_simulated=False):
    if use_simulated:
        return {
            "btts": 60 if equipo_id == 1001 else 60,
            "over15": 80 if equipo_id == 1001 else 80,
            "under15": 20,
            "over25": 40 if equipo_id == 1001 else 40,
            "under25": 60
        }

    try:
        url = f"{BASE_URL}/fixtures?team={equipo_id}&last=50&season={SEASON}"
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        btts_count = 0
        over15_count = 0
        under15_count = 0
        over25_count = 0
        under25_count = 0
        total_partidos = 0

        for match in data.get("response", [])[:20]:
            goles_local = match["goals"]["home"]
            goles_visitante = match["goals"]["away"]

            if not isinstance(goles_local, (int, float)) or not isinstance(goles_visitante, (int, float)):
                continue

            total_goles = goles_local + goles_visitante
            total_partidos += 1

            if goles_local > 0 and goles_visitante > 0:
                btts_count += 1
            if total_goles > 1.5:
                over15_count += 1
            if total_goles < 1.5:
                under15_count += 1
            if total_goles > 2.5:
                over25_count += 1
            if total_goles < 2.5:
                under25_count += 1

        if total_partidos == 0:
            return {"btts": 0, "over15": 0, "under15": 0, "over25": 0, "under25": 0}

        return {
            "btts": round((btts_count / total_partidos) * 100),
            "over15": round((over15_count / total_partidos) * 100),
            "under15": round((under15_count / total_partidos) * 100),
            "over25": round((over25_count / total_partidos) * 100),
            "under25": round((under25_count / total_partidos) * 100)
        }
    except requests.Timeout:
        return {"btts": 0, "over15": 0, "under15": 0, "over25": 0, "under25": 0}
    except requests.RequestException:
        return {"btts": 0, "over15": 0, "under15": 0, "over25": 0, "under25": 0}

def calcular_probabilidades_combinadas(prob_local, prob_away):
    return {
        "btts": round((prob_local["btts"] + prob_away["btts"]) / 2),
        "over15": round((prob_local["over15"] + prob_away["over15"]) / 2),
        "over25": round((prob_local["over25"] + prob_away["over25"]) / 2)
    }

if __name__ == "__main__":
    try:
        output_lines = []
        def custom_print(*args, **kwargs):
            line = " ".join(str(arg) for arg in args)
            output_lines.append(line)

        picks_valiosos = []
        output_file = f"picks_{datetime.now(pytz.timezone('America/Mexico_City')).strftime('%Y%m%d')}.csv"
        logging.debug(f"Iniciando script. Archivo de salida: {output_file}")

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Liga', 'Partido', 'Hora MX', 'Hora ES', 'Cuotas', 'Over 2.5', 'BTTS', 'H2H', 'Predicción', 'Pick', 'Advertencia', 'Score', 'Probabilidades Partido'])

            # Intentar obtener partidos reales, si falla usar simulados
            partidos = obtener_partidos_rango_fechas()
            if not partidos:
                custom_print("⚠️ No se encontraron partidos válidos en el rango de fechas. Usando datos simulados.")
                partidos = obtener_partidos_rango_fechas(use_simulated=True)

            if not partidos:
                custom_print("❌ Error: No se pudieron obtener partidos ni simulados.")
                for line in output_lines:
                    print(line)
                sys.exit(1)

            for p in partidos:
                use_simulated = p["id_fixture"] == 9999  # Usar datos simulados si el fixture es simulado
                logging.debug(f"Procesando partido: {p['local']} vs {p['visitante']} (Simulado: {use_simulated})")

                cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1, use_simulated)
                cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5, use_simulated)
                cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10, use_simulated)

                cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
                cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

                hora_mex, hora_esp = convertir_horas(p["hora_utc"])

                stats_local = obtener_estadisticas_equipo(p["home_id"], use_simulated)
                stats_away = obtener_estadisticas_equipo(p["away_id"], use_simulated)
                h2h_stats = obtener_h2h(p["home_id"], p["away_id"], use_simulated)
                stats_local["nombre"] = p["local"]
                stats_away["nombre"] = p["visitante"]

                goles_local_pred, goles_away_pred = predecir_marcador(stats_local, stats_away, h2h_stats)

                pick = elegir_pick(p, goles_local_pred, goles_away_pred, cuotas_ml, cuota_over, cuota_btts, h2h_stats, stats_local, stats_away, use_simulated)
                cuota_principal = pick.split("@")[-1].strip() if "@" in pick else "0"
                score = calcular_score(stats_local, stats_away, goles_local_pred, goles_away_pred, cuota_principal, h2h_stats, pick)

                prob_local = calcular_probabilidades_btts_over(p["home_id"], use_simulated)
                prob_away = calcular_probabilidades_btts_over(p["away_id"], use_simulated)
                prob_combinada = calcular_probabilidades_combinadas(prob_local, prob_away)

                advertencia = evaluar_advertencia(pick, stats_local, stats_away, h2h_stats)
                score_text = interpretar_score(score)
                pick_display = f"{pick} ⭐" if score >= 4 and "❌" not in pick else pick

                custom_print(f"⚽️ {p['liga']}: {p['local']} vs {p['visitante']}")
                custom_print(f"🕐 Hora: 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}")
                custom_print(f"📊 Promedios: {p['local']} {stats_local['gf']} GF / {stats_local['gc']} GC | {p['visitante']} {stats_away['gf']} GF / {stats_away['gc']} GC")
                custom_print(f"🔮 Predicción: {p['local']} {goles_local_pred} - {goles_away_pred} {p['visitante']}")
                custom_print(f"🎯 {pick_display}")
                custom_print(score_text)
                custom_print(f"📈 Probabilidades: BTTS {prob_combinada['btts']}% | Over 1.5 {prob_combinada['over15']}% | Over 2.5 {prob_combinada['over25']}%")
                custom_print(f"🧠 Forma: {stats_local['forma']} | {stats_away['forma']}")
                custom_print(f"📊 H2H: {h2h_stats['record']} | Goles Promedio: {p['local']} {h2h_stats['home_avg_goals']} - {h2h_stats['away_avg_goals']} {p['visitante']} | Tarjetas Promedio: {h2h_stats['avg_total_cards']}" if h2h_stats["total_matches"] > 0 else f"📊 H2H: No hay datos disponibles")
                custom_print(f"📎 Tarjetas: {stats_local['tarjetas_amarillas']} vs {stats_away['tarjetas_amarillas']} | Corners: {stats_local['corners']} vs {stats_away['corners']}")
                if advertencia:
                    custom_print(advertencia)
                custom_print("-" * 58)

                if score >= 4 and "❌" not in pick:
                    picks_valiosos.append({
                        "liga": p["liga"],
                        "partido": f"{p['local']} vs {p['visitante']}",
                        "pick": pick_display,
                        "score": score_text
                    })

                writer.writerow([
                    p["liga"],
                    f"{p['local']} vs {p['visitante']}",
                    hora_mex,
                    hora_esp,
                    f"🏠 {cuotas_ml[0]['odd'] if cuotas_ml and len(cuotas_ml) > 0 else '❌'} | 🤝 {cuotas_ml[1]['odd'] if cuotas_ml and len(cuotas_ml) > 1 else '❌'} | 🛫 {cuotas_ml[2]['odd'] if cuotas_ml and len(cuotas_ml) > 2 else '❌'}",
                    cuota_over,
                    cuota_btts,
                    f"{h2h_stats['record']} | Goles Promedio: {p['local']} {h2h_stats['home_avg_goals']} - {h2h_stats['away_avg_goals']} {p['visitante']} | Tarjetas Promedio: {h2h_stats['avg_total_cards']}" if h2h_stats["total_matches"] > 0 else "No hay datos H2H",
                    f"{p['local']} {goles_local_pred} - {goles_away_pred} {p['visitante']}",
                    pick_display,
                    advertencia,
                    score_text,
                    f"BTTS {prob_combinada['btts']}% | Over 1.5 {prob_combinada['over15']}% | Over 2.5 {prob_combinada['over25']}%"
                ])

                time.sleep(1)

            for line in output_lines:
                print(line)

            if picks_valiosos:
                print("\n📊 Resumen de partidos ordenados por horario:")
                for pick in picks_valiosos:
                    print(f"{pick['liga']}: {pick['partido']} - {pick['pick']} ({pick['score']})")

            print("✅ Script finalizado.")
            sys.exit(0)

    except Exception as e:
        for line in output_lines:
            print(line)
        print(Fore.RED + f"❌ Error inesperado: {e}" + Style.RESET_ALL)
        sys.exit(1)
