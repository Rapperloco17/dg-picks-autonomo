import requests
from datetime import datetime
import os
import pytz

# ===================== CONFIGURACIÓN =====================
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY").strip()
BASE_URL = "https://api.sportradar.com/tennis/trial/v2/en"

# ===================== FUNCIONES PRINCIPALES =====================
def obtener_partidos_hoy():
    fecha = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/schedules/{fecha}/schedule.json?api_key={SPORTRADAR_API_KEY}"

    try:
        response = requests.get(url)
        if response.status_code == 403:
            print("❌ Error 403: No estás autorizado o se excedió el límite de uso.")
            return []
        elif response.status_code != 200:
            print(f"❌ Error al obtener partidos ({response.status_code})")
            return []

        data = response.json()
        return data.get("sport_events", [])
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []

def preparar_picks_simulados(partidos):
    picks = []

    for partido in partidos:
        try:
            id_partido = partido["id"]
            competidores = partido["competitors"]
            torneo = partido.get("tournament", {}).get("name", "Torneo desconocido")
            hora_utc = partido.get("scheduled", "")[:16].replace("T", " ")

            jugador1 = competidores[0]["name"]
            jugador2 = competidores[1]["name"]

            pick = {
                "partido": f"{jugador1} vs {jugador2}",
                "torneo": torneo,
                "hora": hora_utc,
                "pick": f"{jugador1} rompe el servicio en el primer set",
                "justificacion": "Jugador con buen return contra un rival débil al servicio (análisis simulado)."
            }
            picks.append(pick)
        except:
            continue

    return picks

def imprimir_picks_estilo_dg(picks):
    for p in picks:
        print(f"🎾 {p['partido']} – {p['torneo']}")
        print(f"🕐 Hora programada: {p['hora']} (UTC)")
        print(f"📌 Pick: {p['pick']}")
        print(f"📊 {p['justificacion']}")
        print("✅ Valor detectado en la cuota\n")

# ===================== EJECUCIÓN =====================
if __name__ == "__main__":
    print("🔍 Buscando partidos de hoy en Sportradar...")
    partidos = obtener_partidos_hoy()

    if not partidos:
        print("⚠️ No se encontraron partidos o hubo un error.")
    else:
        print(f"🎾 {len(partidos)} partidos encontrados.")
        picks = preparar_picks_simulados(partidos)
        imprimir_picks_estilo_dg(picks)
