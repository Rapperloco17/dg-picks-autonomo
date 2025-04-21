# fouls_stats.py – Análisis completo con árbitro (permiso/rigor)

import requests
from utils.telegram import enviar_mensaje

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"
ADMIN_CHAT_ID = "7450739156"


def analizar_faltas(fixture):
    try:
        league_id = fixture['league']['id']
        season = fixture['league']['season']
        home = fixture['teams']['home']
        away = fixture['teams']['away']
        referee = fixture['fixture'].get('referee', None)

        def obtener_faltas(team_id):
            params = {"league": league_id, "season": season, "team": team_id}
            res = requests.get(STATS_URL, headers=HEADERS, params=params)
            data = res.json().get("response", {})
            if not data:
                return 0, 0
            total = data.get("fixtures", {}).get("played", {}).get("total", 1)
            fouls = data.get("fouls", {})
            if not fouls:
                return 0, 0
            cometidas = fouls.get("committed", 0)
            recibidas = fouls.get("drawn", 0)
            return round(cometidas / total, 2), round(recibidas / total, 2)

        faltas_home, recibidas_home = obtener_faltas(home['id'])
        faltas_away, recibidas_away = obtener_faltas(away['id'])

        total_fisico = faltas_home + faltas_away + recibidas_home + recibidas_away

        justificacion = []

        if faltas_home >= 12:
            justificacion.append(f"{home['name']} comete muchas faltas: {faltas_home}")
        if faltas_away >= 12:
            justificacion.append(f"{away['name']} comete muchas faltas: {faltas_away}")
        if recibidas_home >= 11:
            justificacion.append(f"{home['name']} recibe muchas faltas: {recibidas_home}")
        if recibidas_away >= 11:
            justificacion.append(f"{away['name']} recibe muchas faltas: {recibidas_away}")

        # Ajuste por árbitro si se detecta
        if referee:
            promedio_arbitro = promedio_faltas_arbitro(referee)
            if promedio_arbitro:
                justificacion.append(f"Árbitro {referee} promedia {promedio_arbitro} faltas por partido")
                total_fisico += promedio_arbitro * 0.15

        if total_fisico >= 28:
            mensaje = f"\ud83d\udd39 <b>PROP DE FALTAS – SIN CUOTA</b>\n"
            mensaje += f"<b>Partido:</b> {home['name']} vs {away['name']}\n"
            mensaje += f"<b>Pick:</b> Más de 27.5 faltas totales\n"
            mensaje += f"<b>Promedio combinado:</b> {round(total_fisico, 2)}\n"
            mensaje += f"<b>Justificación:</b> " + "; ".join(justificacion)
            mensaje += "\n⚠️ Cuota no disponible – revisar manualmente"
            enviar_mensaje(mensaje, canal=ADMIN_CHAT_ID)

    except Exception as e:
        print(f"\u26a0\ufe0f Error en fouls_stats.py: {e}")


def promedio_faltas_arbitro(nombre):
    # Base de árbitros manual para ejemplo – puedes expandirla
    arbitros = {
        "Mateu Lahoz": 27.2,
        "Sánchez Martínez": 28.6,
        "Michael Oliver": 22.1,
        "Daniele Orsato": 25.9,
        "Anthony Taylor": 20.4,
        "Jesus Gil Manzano": 30.3
    }
    return arbitros.get(nombre, 24.0)
