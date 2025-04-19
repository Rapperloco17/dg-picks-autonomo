# soccer_generator.py (conectado a API con ligas y temporadas correctas)

from utils.api_football import obtener_partidos_de_liga
from datetime import datetime
import json

# Cargar ligas válidas con nombres (ya debe venir como dict desde JSON)
with open("utils/leagues_whitelist_ids.json") as f:
    ligas_validas = json.load(f)

# Fecha de hoy
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# Resultado de conteo por liga
resultados = {}

for liga_id, liga_nombre in ligas_validas.items():
    data = obtener_partidos_de_liga(int(liga_id), fecha_hoy)
    cantidad = len(data.get("response", []))
    resultados[liga_nombre] = cantidad

print("\nResumen de partidos encontrados hoy:")
for liga, cantidad in resultados.items():
    print(f"- {liga}: {cantidad} partidos")

# Aquí seguiría el análisis de valor, forma, racha y construcción de picks
# (esto ya lo tienes o se conecta a modules como soccer_stats.py o formato.py)

