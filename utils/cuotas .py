
# utils/cuotas.py

import requests

API_KEY = "137992569bc2352366c01e6928577b2d"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

def obtener_cuota_bet365(deporte, mercado="h2h"):
    """
    Obtiene la cuota para un evento del deporte y mercado especificado desde Bet365
    """
    deportes = {
        "mlb": "baseball_mlb",
        "nba": "basketball_nba",
        "futbol": "soccer_mexico_liga_mx",
        "tenis": "tennis_atp"
    }

    deporte_codigo = deportes.get(deporte.lower())
    if not deporte_codigo:
        return None

    url = f"{BASE_URL}/{deporte_codigo}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": mercado,
        "bookmakers": "bet365"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if not data or "bookmakers" not in data[0]:
            return None

        cuota = data[0]["bookmakers"][0]["markets"][0]["outcomes"][0]["price"]
        return cuota
    except Exception as e:
        print(f"Error al obtener cuota: {e}")
        return None

def validar_valor_cuota(cuota, min_valor=1.70, max_valor=2.20):
    return cuota is not None and min_valor <= cuota <= max_valor
