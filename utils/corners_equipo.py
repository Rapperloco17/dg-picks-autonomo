
# corners_equipo.py – Detección de equipos que generan o permiten muchos córners (props individuales)

import requests
from utils.telegram import enviar_mensaje

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"
ADMIN_CHAT_ID = "7450739156"


def analizar_corners_por_equipo(fixture):
    try:
        league_id = fixture['league']['id']
        season = fixture['league']['season']
        home = fixture['teams']['home']
        away = fixture['teams']['away']

        def obtener_stats(team_id):
            params = {"league": league_id, "season": season, "team": team_id}
            res = requests.get(STATS_URL, headers=HEADERS, params=params)
            data = res.json().get("response", {})
            if not data:
                return 0, 0
            total = data.get("fixtures", {}).get("played", {}).get("total", 1)
            corners = data.get("corners", {})
            if not corners:
                return 0, 0
            a_favor = corners.get("for", {}).get("total", 0)
            en_contra = corners.get("against", {}).get("total", 0)
            return round(a_favor / total, 2), round(en_contra / total, 2)

        # Obtener promedios individuales
        home_for, home_against = obtener_stats(home['id'])
        away_for, away_against = obtener_stats(away['id'])

        # Umbrales configurables
        mensaje = ""
        if home_for >= 6.0:
            mensaje += f"\ud83c\udfe0 <b>{home['name']} genera muchos córners (prom: {home_for})</b>\n"
        if away_against >= 5.5:
            mensaje += f"\u26d4 {away['name']} permite muchos córners (prom: {away_against})\n"
        if away_for >= 6.0:
            mensaje += f"\ud83d\ude97 <b>{away['name']} genera muchos córners (prom: {away_for})</b>\n"
        if home_against >= 5.5:
            mensaje += f"\u26a0\ufe0f {home['name']} permite muchos córners (prom: {home_against})\n"

        if mensaje:
            full = f"\ud83d\udea9 <b>PROP DE C\u00d3RNERS INDIVIDUAL</b>\n"
            full += f"<b>Partido:</b> {home['name']} vs {away['name']}\n"
            full += mensaje
            full += "\n⚠️ Cuota no disponible – revisar manualmente"
            enviar_mensaje(full, canal=ADMIN_CHAT_ID)

    except Exception as e:
        print(f"\u26a0\ufe0f Error en corners_equipo.py: {e}")
