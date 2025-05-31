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

def analizar_partido(partido):
    match_id = partido["id"]
    torneo = partido.get("tournament", {}).get("name", "Torneo desconocido")
    hora_utc = partido.get("scheduled", "")[:16].replace("T", " ")
    competidores = partido.get("competitors", [])

    if len(competidores) != 2:
        return None, None

    jugador1 = competidores[0]["name"]
    jugador2 = competidores[1]["name"]

    stats = obtener_estadisticas(match_id)
    if not stats or "statistics" not in stats.get("sport_event_status", {}):
        print(f"⚠️ Sin stats para {jugador1} vs {jugador2}")
        return None, None

    try:
        estadisticas = stats["sport_event_status"]["statistics"]["competitors"]
        stats1 = estadisticas[0]["statistics"]
        stats2 = estadisticas[1]["statistics"]

        p1_return = stats1.get("receiving_points_won_pct", 0)
        p1_breaks = stats1.get("break_points_converted", 0)
        p2_1st_serve = stats2.get("first_serve_pct", 100)
        p2_breaks_faced = stats2.get("break_points_faced", 0)

        p2_return = stats2.get("receiving_points_won_pct", 0)
        p2_breaks = stats2.get("break_points_converted", 0)
        p1_1st_serve = stats1.get("first_serve_pct", 100)
        p1_breaks_faced = stats1.get("break_points_faced", 0)

        # Logs de debug
        print(f"📊 {jugador1} (return {p1_return}%, breaks {p1_breaks}) vs {jugador2} (1st serve {p2_1st_serve}%)")
        print(f"📊 {jugador2} (return {p2_return}%, breaks {p2_breaks}) vs {jugador1} (1st serve {p1_1st_serve}%)")

        pick_rompe = None
        pick_no_rompe = None

        # ✅ Rompe
        if p1_return >= 35 and p2_1st_serve <= 65 and p1_breaks >= 1 and p2_breaks_faced >= 1:
            pick_rompe = {
                "partido": f"{jugador1} vs {jugador2}",
                "torneo": torneo,
                "hora": hora_utc,
                "pick": f"{jugador1} rompe el servicio en el primer set",
                "justificacion": f"{jugador1} gana {p1_return}% al resto y ha convertido {p1_breaks} breaks. {jugador2} solo acierta {p2_1st_serve}% con el primer saque y ha enfrentado {p2_breaks_faced} breaks."
            }

        # ❌ No rompe
        if p2_return <= 28 and p1_1st_serve >= 68 and p2_breaks == 0:
            pick_no_rompe = {
                "partido": f"{jugador2} vs {jugador1}",
                "torneo": torneo,
                "hora": hora_utc,
                "pick": f"{jugador2} NO rompe el servicio en el primer set",
                "justificacion": f"{jugador2} solo gana {p2_return}% al resto, no ha convertido breaks y enfrenta a un rival con {p1_1st_serve}% de primer servicio."
            }

        return pick_rompe, pick_no_rompe
    except Exception as e:
        print(f"⚠️ Error en análisis de {jugador1} vs {jugador2}: {e}")
        return None, None

def imprimir_picks_estilo_dg(picks, tipo):
    print(f"\n📌 PICKS: {tipo.upper()} 🔽")
    for p in picks:
        print(f"🎾 {p['partido']} – {p['torneo']}")
        print(f"🕐 Hora: {p['hora']} UTC")
        print(f"📌 Pick: {p['pick']}")
        print(f"📊 {p['justificacion']}")
        print("✅ Valor detectado en la cuota\n")

# ===================== EJECUCIÓN =====================
if __name__ == "__main__":
    print("🔍 Buscando partidos y estadísticas reales...")
    partidos = obtener_partidos_hoy()

    picks_rompe = []
    picks_no_rompe = []

    if not partidos:
        print("⚠️ No se encontraron partidos o hubo un error.")
    else:
        for p in partidos:
            pick1, pick2 = analizar_partido(p)
            if pick1:
                picks_rompe.append(pick1)
            if pick2:
                picks_no_rompe.append(pick2)

        if picks_rompe:
            imprimir_picks_estilo_dg(picks_rompe, "rompe")
        else:
            print("\n❌ No se detectaron jugadores que probablemente rompan el servicio.")

        if picks_no_rompe:
            imprimir_picks_estilo_dg(picks_no_rompe, "NO rompe")
        else:
            print("❌ No se detectaron jugadores que probablemente NO rompan el servicio.")
