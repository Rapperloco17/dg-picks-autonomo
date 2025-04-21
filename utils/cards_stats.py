# cards_stats.py – Ahora con uso de cache para evitar repetir requests

import requests
from utils.telegram import enviar_mensaje
from utils.cache import cargar_fixture_cache

FOOTBALL_API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"
ADMIN_CHAT_ID = "7450739156"


def analizar_tarjetas(fixture):
    try:
        fixture_id = fixture['fixture']['id']
        full_fixture = cargar_fixture_cache(fixture_id)
        if not full_fixture:
            return

        league_id = full_fixture['league']['id']
        season = full_fixture['league']['season']
        home = full_fixture['teams']['home']
        away = full_fixture['teams']['away']
        referee = full_fixture['fixture'].get('referee', None)

        def obtener_tarjetas_promedio(team_id):
            params = {"league": league_id, "season": season, "team": team_id}
            res = requests.get(STATS_URL, headers=HEADERS, params=params)
            data = res.json().get("response", {})
            if not data:
                return 0
            total = data.get("fixtures", {}).get("played", {}).get("total", 1)
            amarillas = data.get("cards", {}).get("yellow", {}).get("total", 0)
            rojas = data.get("cards", {}).get("red", {}).get("total", 0)
            promedio = (amarillas + (2 * rojas)) / total if total else 0
            return round(promedio, 2)

        promedio_home = obtener_tarjetas_promedio(home['id'])
        promedio_away = obtener_tarjetas_promedio(away['id'])
        total_promedio = round(promedio_home + promedio_away, 2)

        justificacion = []

        if promedio_home >= 2.5:
            justificacion.append(f"{home['name']} promedia {promedio_home} tarjetas por partido")
        if promedio_away >= 2.5:
            justificacion.append(f"{away['name']} promedia {promedio_away} tarjetas por partido")

        if referee:
            ref_data = obtener_info_arbitro(referee)
            if ref_data:
                justificacion.append(f"Árbitro {referee} promedia {ref_data} tarjetas por partido")
                total_promedio += ref_data * 0.2

        if total_promedio >= 5:
            mensaje = f"\ud83d\udd39 <b>PROP DE TARJETAS – SIN CUOTA</b>\n"
            mensaje += f"<b>Partido:</b> {home['name']} vs {away['name']}\n"
            mensaje += f"<b>Pick:</b> Más de 4.5 tarjetas totales\n"
            mensaje += f"<b>Promedio combinado:</b> {total_promedio}\n"
            mensaje += "<b>Justificación:</b> " + "; ".join(justificacion)
            mensaje += "\n⚠️ Cuota no disponible – revisar manualmente"

            enviar_mensaje(mensaje, canal=ADMIN_CHAT_ID)

    except Exception as e:
        print(f"\u26a0\ufe0f Error en cards_stats.py: {e}")


def obtener_info_arbitro(nombre):
    arbitros_estrictos = {
        "Antonio Mateu Lahoz": 6.1,
        "Sánchez Martínez": 5.9,
        "Daniele Orsato": 5.8,
        "Michael Oliver": 5.2,
        "Clément Turpin": 4.8
    }
    return arbitros_estrictos.get(nombre, 4.0)
