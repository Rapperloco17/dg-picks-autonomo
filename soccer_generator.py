# soccer_generator.py (corregido para usar lista de IDs correctamente)

from utils.api_football import obtener_partidos_de_liga
from datetime import datetime
import json

# Cargar solo la lista de IDs permitidos desde el JSON
with open("utils/leagues_whitelist_ids.json") as f:
    lista_ids = json.load(f)["allowed_league_ids"]

# Fecha de hoy
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# Resultado de conteo por liga
resultados = {}

for liga_id in lista_ids:
    try:
        data = obtener_partidos_de_liga(int(liga_id), fecha_hoy)
        cantidad = len(data.get("response", []))
        resultados[liga_id] = cantidad
    except Exception as e:
        print(f"\u26a0\ufe0f Error con liga {liga_id}:", e)
        resultados[liga_id] = 0

print("\nResumen de partidos encontrados hoy:")
for liga_id, cantidad in resultados.items():
    print(f"- Liga {liga_id}: {cantidad} partidos")

# Aquí sigue el análisis y generación de picks
