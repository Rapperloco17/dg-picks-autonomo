# corners_stats.py – Análisis de córners combinados por partido (total corners)

import requests
from utils.telegram import enviar_mensaje

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"
ADMIN_CHAT_ID = "7450739156"


def analizar_corners_avanzado(fixture):
    try:
        league_id = fixture['league']['id']
        season = fixture['league']['season']
        home = fixture['teams']['home']
        away = fixture['teams']['away']

        def corners_promedio(team_id):
            params = {"league": league_id, "season": season, "team": team_id}
            res = requests.get(STATS_URL, headers=HEADERS, params=params)
            data = res.json().get("response", {})
            if not data:
                return 0
            total = data.get("fixtures", {}).get("played", {}).get("total", 1)
            corners = data.get("corners", {})
            if not corners:
                return 0
            avg = corners.get("for", {}).get("total", 0) + corners.get("against", {}).get("total", 0)
            return round(avg / total, 2) if total else 0

        avg_home = corners_promedio(home['id'])
        avg_away = corners_promedio(away['id'])
        total_avg = round((avg_home + avg_away) / 2, 2)

        if total_avg >= 9.0:
            texto = f"\ud83d\udea9 <b>PROP DE C\u00d3RNERS TOTALES</b>\n"
            texto += f"<b>Partido:</b> {home['name']} vs {away['name']}\n"
            texto += f"<b>Pick:</b> Más de 8.5 córners totales\n"
            texto += f"<b>Promedio conjunto:</b> {total_avg}\n"
            texto += f"<b>Justificación:</b> Ambos equipos generan o permiten buen volumen de córners.\n"
            texto += f"\n⚠️ Cuota no disponible – revisar manualmente"

            enviar_mensaje(texto, canal=ADMIN_CHAT_ID)

    except Exception as e:
        print(f"\u26a0\ufe0f Error en corners_stats.py: {e}")
