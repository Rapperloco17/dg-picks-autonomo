import requests
from datetime import datetime
import os
import pytz

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY").strip()
BASE_URL = "https://api.sportradar.com/tennis/trial/v2/en"

def obtener_partidos_hoy():
    fecha = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/schedules/{fecha}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Error al obtener partidos ({response.status_code})")
            return []
        data = response.json()
        return data.get("sport_events", [])
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []

def obtener_estadisticas(match_id):
    url = f"{BASE_URL}/matches/{match_id}/summary.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.json()
    except:
        return None

def analizar_partido_y_generar_pick(partido):
    match_id = partido["id"]
    torneo = partido.get("tournament", {}).get("name", "Torneo desconocido")
    hora_utc = partido.get("scheduled", "")[:16].replace("T", " ")
    competidores = partido.get("competitors", [])
    
    if len(competidores) != 2:
        return None

    jugador1 = competidores[0]["name"]
    jugador2 = competidores[1]["name"]

    stats = obtener_estadisticas(match_id)
    if not stats or "statistics" not in stats.get("sport_event_status", {}):
        print(f"⚠️ No hay stats disponibles para {jugador1} vs {jugador2}")
        return None

    estadisticas = stats["sport_event_status"]["statistics"]

    try:
        stats1 = estadisticas["competitors"][0]["statistics"]
        stats2 = estadisticas["competitors"][1]["statistics"]

        # Valores clave
        p1_return = stats1.get("receiving_points_won_pct", 0)
        p1_breaks = stats1.get("break_points_converted", 0)
        p2_1st_serve = stats2.get("first_serve_pct", 100)
        p2_breaks_faced = stats2.get("break_points_faced", 0)

        # Debug en consola/logs
        print(f"📊 {jugador1} (return: {p1_return}%, breaks convertidos: {p1_breaks}) | {jugador2} (1st serve: {p2_1st_serve}%, breaks enfrentados: {p2_breaks_faced})")

        # Criterios de rompimiento
        if p1_return >= 35 and p2_1st_serve <= 65 and p1_breaks >= 1 and p2_breaks_faced >= 1:
            return {
                "partido": f"{jugador1} vs {jugador2}",
                "torneo": torneo,
                "hora": hora_utc,
                "pick": f"{jugador1} rompe el servicio en el primer set",
                "justificacion": f"{jugador1} gana {p1_return}% al resto y ha convertido {p1_breaks} break points. {jugador2} solo acierta {p2_1st_serve}% con el primer saque y ha enfrentado {p2_breaks_faced} breaks."
            }
    except Exception as e:
        print(f"⚠️ Error en análisis de {jugador1} vs {jugador2}: {e}")
        return None

    return None

def imprimir_picks_estilo_dg(picks):
    for p in picks:
        print(f"🎾 {p['partido']} – {p['torneo']}")
        print(f"🕐 Hora programada: {p['hora']} (UTC)")
        print(f"📌 Pick: {p['pick']}")
        print(f"📊 {p['justificacion']}")
        print("✅ Valor detectado en la cuota\n")

# ===================== EJECUCIÓN =====================
if __name__ == "__main__":
    print("🔍 Buscando partidos y estadísticas reales...")
    partidos = obtener_partidos_hoy()

    if not partidos:
        print("⚠️ No se encontraron partidos o hubo un error.")
    else:
        picks = []
        for p in partidos:
            pick = analizar_partido_y_generar_pick(p)
            if pick:
                picks.append(pick)

        if picks:
            imprimir_picks_estilo_dg(picks)
        else:
            print("❌ No se encontraron picks con valor para rompimiento en primer set.")
