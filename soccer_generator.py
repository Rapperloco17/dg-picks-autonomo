# soccer_generator.py (completo y corregido con integración real)

from utils.api_football import obtener_partidos_de_liga
from datetime import datetime
import json

# Cargar ligas válidas con nombres (desde clave 'allowed_league_ids' en el JSON)
with open("utils/leagues_whitelist_ids.json") as f:
    ligas_validas = json.load(f)["allowed_league_ids"]

# Fecha de hoy
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# Resultado de conteo por liga
resultados = {}

for liga_id, liga_nombre in ligas_validas.items():
    try:
        data = obtener_partidos_de_liga(int(liga_id), fecha_hoy)
        cantidad = len(data.get("response", []))
        resultados[liga_nombre] = cantidad
    except Exception as e:
        print(f"\u26a0\ufe0f Error con liga {liga_id} ({liga_nombre}):", e)
        resultados[liga_nombre] = 0

print("\nResumen de partidos encontrados hoy:")
for liga, cantidad in resultados.items():
    print(f"- {liga}: {cantidad} partidos")

# Aquí sigue el análisis y generación de picks
