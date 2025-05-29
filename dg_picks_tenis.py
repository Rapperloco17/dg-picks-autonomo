import requests
import json
from datetime import datetime

API_KEY = "62445b378b11906da093a6ae6513242ae3de2134660c3aefbf74872bbcdccdc2"
BASE_URL = "https://api.api-tennis.com/tennis/"
HEADERS = {"x-api-key": API_KEY}

ATP_ID = "265"
CHALLENGER_ID = "281"

# Simulamos función para obtener fixtures del día (luego se conecta al endpoint real)
def obtener_fixtures():
    print("📥 Obteniendo partidos ATP y Challenger del día...")
    # Aquí iría la lógica real con requests a /fixtures por torneo
    return [
        {
            "match": "Giovanni Fonio vs Titouan Droguet",
            "jugador_1": "Giovanni Fonio",
            "jugador_2": "Titouan Droguet",
            "hora": "03:00",
            "superficie": "Clay",
            "stats": {
                "fonio": {"breaks_1set": 7, "ultimos_partidos": 9},
                "droguet": {"bp_concedidos": 1.8, "saque_debil": True}
            }
        }
    ]

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
            print(f"Hora: {pick['hora']} | Superficie: {pick['superficie']}")
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

