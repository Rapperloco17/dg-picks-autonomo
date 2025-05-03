import json
from utils.api_football import API_KEY, API_URL

# Cargar las ligas válidas desde el archivo
with open("utils/leagues_whitelist_ids.json", "r") as f:
    LIGAS = json.load(f)  # Ya NO usamos ["allowed_league_ids"], porque es una lista directa

# Ejemplo de uso posterior en tu código
for liga_id in LIGAS:
    # Aquí va el código que hace algo con cada liga
    print(f"Procesando liga {liga_id}")
