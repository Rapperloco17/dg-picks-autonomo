import requests
from datetime import datetime

API_KEY = "62445b378b11906da093a6ae6513242ae3de2134660c3aefbf74872bbcdccdc2"
BASE_URL = "https://api.api-tennis.com"
CATEGORIAS = "ATP,Challenger"

def obtener_partidos_dia():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/tennis/?method=get_matches&date={hoy}&category={CATEGORIAS}&APIkey={API_KEY}"

    response = requests.get(url)
    data = response.json()

    if not data.get("result"):
        print("⚠️ No se encontraron partidos.")
        return []

    return data["result"]

def obtener_stats_jugador(nombre_jugador):
    url = f"{BASE_URL}/tennis/?method=get_players_stats&player={nombre_jugador}&APIkey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if not data.get("result"):
        return None

    stats = data["result"][0]  # solo tomamos el más reciente
    return stats

def analizar_rompimiento(stats):
    if not stats:
        return 0

    try:
        clay_stats = stats["surface"]["Clay"]
        breaks = clay_stats["return_games_won"]
        return float(breaks)
    except:
        return 0

def generar_picks_rompimiento():
    partidos = obtener_partidos_dia()
    picks = []

    for partido in partidos:
        jugador1 = partido["player1"]
        jugador2 = partido["player2"]
        torneo = partido.get("tournament", "Sin torneo")
        hora = partido.get("match_time", "Hora desconocida")

        stats1 = obtener_stats_jugador(jugador1)
        stats2 = obtener_stats_jugador(jugador2)

        romp1 = analizar_rompimiento(stats1)
        romp2 = analizar_rompimiento(stats2)

        if romp1 >= 25:  # criterio base: al menos 25% de games al resto ganados
            pick = f"🎾 {jugador1} rompe el servicio en el 1er set\n🏆 Torneo: {torneo} | 🕐 Hora: {hora}"
            pick += f"\n📊 {jugador1} gana {romp1:.1f}% de juegos al resto en arcilla."
            picks.append(pick)

        if romp2 >= 25:
            pick = f"🎾 {jugador2} rompe el servicio en el 1er set\n🏆 Torneo: {torneo} | 🕐 Hora: {hora}"
            pick += f"\n📊 {jugador2} gana {romp2:.1f}% de juegos al resto en arcilla."
            picks.append(pick)

    if picks:
        for p in picks:
            print("\n🔐 PICK DETECTADO 🔐\n" + p)
    else:
        print("❌ No se detectaron picks de rompimiento con valor hoy.")

# Ejecutar
if __name__ == "__main__":
    generar_picks_rompimiento()
