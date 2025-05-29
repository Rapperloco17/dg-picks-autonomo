import requests
import json
from datetime import datetime

API_KEY = "62445b378b11906da093a6ae6513242ae3de2134660c3aefbf74872bbcdccdc2"
BASE_URL = "https://api.api-tennis.com/tennis/"

ATP_ID = "265"
CHALLENGER_ID = "281"

# Solo imprime la estructura de los fixtures reales para inspección
def obtener_fixtures():
    print("📥 Inspeccionando estructura de fixtures reales desde API...")
    for event_id in [ATP_ID, CHALLENGER_ID]:
        url = f"{BASE_URL}?method=get_fixtures&APIkey={API_KEY}&eventId={event_id}"
        try:
            response = requests.get(url)
            data = response.json()
            print(f"\n📦 Fixture recibido para evento {event_id}:")
            print(json.dumps(data, indent=2))
            break  # solo mostramos uno para inspección
        except Exception as e:
            print(f"⚠️ Error al obtener fixtures de evento {event_id}: {e}")

# Mantenemos estructura para no romper ejecución
def analizar_rompimientos(partido):
    return None

def main():
    obtener_fixtures()

if __name__ == "__main__":
    main()
