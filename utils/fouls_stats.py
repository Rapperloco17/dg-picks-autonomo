# fouls_stats.py – Análisis de faltas por equipo y partidos físicos

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

        if total_fisico >= 28:
            mensaje = f"\ud83d\udd39 <b>PROP DE FALTAS – SIN CUOTA</b>\n"
            mensaje += f"<b>Partido:</b> {home['name']} vs {away['name']}\n"
            mensaje += f"<b>Pick:</b> Más de 27.5 faltas totales\n"
            mensaje += f"<b>Promedio conjunto:</b> {total_fisico}\n"
            mensaje += f"<b>Justificación:</b> Partido con mucha intensidad física.\n"
            mensaje += "\n⚠️ Cuota no disponible – revisar manualmente"

            enviar_mensaje(mensaje, canal=ADMIN_CHAT_ID)

    except Exception as e:
        print(f"\u26a0\ufe0f Error en fouls_stats.py: {e}")

