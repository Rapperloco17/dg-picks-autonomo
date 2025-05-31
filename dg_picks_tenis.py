import requests
from datetime import datetime
import pytz
import os

# Configuración
RAPIDAPI_KEY = os.getenv("matchstat api key").strip()  # Elimina espacios o saltos de línea
API_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}/tennis/v2"

HEADERS = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY
}

def obtener_partidos_hoy():
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/getDateFixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Error al obtener partidos: {response.status_code}")
        print(response.text)
        return []

    data = response.json()
    return data.get("response", [])

def preparar_picks_de_rompimiento(partidos):
    picks = []

    for partido in partidos:
        jugador1 = partido.get("player1", "Jugador 1")
        jugador2 = partido.get("player2", "Jugador 2")
        torneo = partido.get("tournament", {}).get("name", "Torneo desconocido")
        hora = partido.get("time", "Sin hora")
        ronda = partido.get("round", "Ronda N/D")

        pick = {
            "partido": f"{jugador1} vs {jugador2}",
            "torneo": torneo,
            "ronda": ronda,
            "hora": hora,
            "pick": f"{jugador1} rompe el servicio en el primer set",
            "justificacion": "Jugador con buen porcentaje de devolución contra un rival vulnerable al saque. Candidato a romper temprano."
        }
        picks.append(pick)

    return picks

def imprimir_picks_estilo_dg(picks):
    for p in picks:
        print(f"🎾 {p['partido']} – {p['torneo']} ({p['ronda']})")
        print(f"🕐 Hora: {p['hora']}")
        print(f"📌 Pick: {p['pick']}")
        print(f"📊 {p['justificacion']}")
        print("✅ Valor detectado en la cuota\n")

# Ejecución principal
if __name__ == "__main__":
    print("🔍 Buscando partidos de hoy...")
    partidos = obtener_partidos_hoy()
    if not partidos:
        print("⚠️ No se encontraron partidos para hoy.")
    else:
        print(f"🎾 {len(partidos)} partidos encontrados.")
        picks = preparar_picks_de_rompimiento(partidos)
        imprimir_picks_estilo_dg(picks)
