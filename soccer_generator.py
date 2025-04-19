# utils/api_football.py (con ajustes completos)

import requests
from datetime import datetime

API_URL = "https://v3.football.api-sports.io"
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"  # ← Tu clave real activa

headers = {
    "x-apisports-key": API_KEY
}

# Ligas permitidas con IDs reales desde leagues_whitelist_ids.json
ligas_validas = {
    39,
        40,
        140,
        144,
        135,
        136,
        78,
        79,
        61,
        62,
        94,
        88,
        203,
        128,
        71,
        72,
        253,
        262,
        256,
        2,
        3,
        848,
        141,
        254,
        291,
        105,
        294,
        103,
        129,
        112,
        292,
        98,
        307
}

# Fecha actual en formato YYYY-MM-DD
fecha_hoy = datetime.now().strftime("%Y-%m-%d")


def obtener_partidos_de_liga(liga_id, fecha):
    params = {
        "league": liga_id,
        "season": 2025,
        "date": fecha
    }
    try:
        response = requests.get(f"{API_URL}/fixtures", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\u26a0\ufe0f Error al conectar con la API para liga {liga_id}:", e)
        return {"response": []}


# Ejemplo de ejecución para testeo directo
if __name__ == "__main__":
    resultados = {}
    for liga_id in ligas_validas:
        data = obtener_partidos_de_liga(liga_id, fecha_hoy)
        resultados[ligas_validas[liga_id]] = len(data.get("response", []))

    print("\nResumen de partidos encontrados hoy:")
    for liga, cantidad in resultados.items():
        print(f"- {liga}: {cantidad} partidos")
