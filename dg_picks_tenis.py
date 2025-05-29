import requests
import json
from datetime import datetime

API_KEY = "62445b378b11906da093a6ae6513242ae3de2134660c3aefbf74872bbcdccdc2"
BASE_URL = "https://api.api-tennis.com/tennis/"

ATP_ID = "265"
CHALLENGER_ID = "281"

# Obtener partidos del día con campos reales de jugadores y hora
def obtener_fixtures():
    print("📥 Consultando partidos reales desde API...")
    hoy = datetime.now().strftime('%Y-%m-%d')
    fixtures = []

    for event_id in [ATP_ID, CHALLENGER_ID]:
        url = f"{BASE_URL}?method=get_fixtures&APIkey={API_KEY}&eventId={event_id}&date_start={hoy}&date_stop={hoy}"
        try:
            response = requests.get(url)
            data = response.json()
            for match in data.get("result", []):
                player1 = match.get("event_first_player", "")
                player2 = match.get("event_second_player", "")
                hora = match.get("event_time", "")[:5]
                ronda = match.get("tournament_round", "")
                fecha = match.get("event_date", hoy)

                fixtures.append({
                    "match": f"{player1} vs {player2}",
                    "jugador_1": player1,
                    "jugador_2": player2,
                    "hora": hora,
                    "fecha": fecha,
                    "ronda": ronda,
                    "superficie": "Desconocida",
                    "stats": {
                        "fonio": {"breaks_1set": 7, "ultimos_partidos": 9},
                        "droguet": {"bp_concedidos": 1.8, "saque_debil": True}
                    }
                })
        except Exception as e:
            print(f"⚠️ Error al obtener fixtures de evento {event_id}: {e}")

    return fixtures

# Simula análisis de rompimiento
def analizar_rompimientos(partido):
    stats = partido["stats"]
    fonio_break_rate = stats["fonio"]["breaks_1set"] / stats["fonio"]["ultimos_partidos"]
    droguet_concede = stats["droguet"]["bp_concedidos"] >= 1.5

    if fonio_break_rate >= 0.7 and droguet_concede:
        return {
            "match": partido["match"],
            "pick": f"{partido['jugador_1']} rompe en el primer set",
            "motivo": "Fonio ha roto el servicio en el primer set en 7 de sus últimos 9 partidos en arcilla. Droguet tiene bajo % de puntos ganados con segundo servicio.",
            "combinada": True,
            "hora": partido["hora"],
            "superficie": partido["superficie"],
            "ronda": partido["ronda"],
            "fecha_generado": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    else:
        return None

# Flujo principal del módulo
def main():
    partidos = obtener_fixtures()
    picks = []

    for partido in partidos:
        pick = analizar_rompimientos(partido)
        if pick:
            picks.append(pick)
            print("\n🎾 Pick generado:")
            print(f"Partido: {pick['match']}")
            print(f"Ronda: {pick['ronda']} | Hora: {pick['hora']} | Superficie: {pick['superficie']}")
            print(f"🔐 Pick: {pick['pick']}")
            print(f"📝 Motivo: {pick['motivo']}")
            if pick['combinada']:
                print("🧨 Este partido tiene potencial para combinada.")

    # Guardar como JSON
    if picks:
        with open("picks_tenis.json", "w") as f:
            json.dump(picks, f, indent=4)
        print(f"\n✅ {len(picks)} pick(s) guardado(s) en 'picks_tenis.json'")
    else:
        print("❌ No se generaron picks hoy.")

if __name__ == "__main__":
    main()
