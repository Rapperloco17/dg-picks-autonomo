# dg_picks_futbol.py
import requests
import datetime

API_KEY = "TU_API_KEY"

# Obtener cuotas desde la API directamente (bet365 = bookmaker 6)
def obtener_cuota_fixture(api_key: str, fixture_id: int, market: str = "over_under", value: float = 2.5):
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}&bookmaker=6"
    headers = {
        "x-apisports-key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data["response"]:
            return None

        for item in data["response"]:
            for bet in item["bets"]:
                if market == "over_under" and "Over" in bet["name"]:
                    for odd in bet["values"]:
                        if str(value) in odd["value"]:
                            return float(odd["odd"])
                elif market == "btts" and bet["name"] == "Both Teams To Score":
                    for odd in bet["values"]:
                        if odd["value"] == "Yes":
                            return float(odd["odd"])

        return None
    except Exception as e:
        print(f"Error al obtener cuota para fixture {fixture_id}: {e}")
        return None

# Lógica base de ejemplo para un partido específico
def analizar_fixture(fixture_id):
    print(f"\nAnalizando fixture {fixture_id}...")

    cuota_o25 = obtener_cuota_fixture(API_KEY, fixture_id, market="over_under", value=2.5)
    cuota_btts = obtener_cuota_fixture(API_KEY, fixture_id, market="btts")

    if cuota_o25:
        print(f"Cuota Over 2.5 goles: {cuota_o25}")
    else:
        print("No se encontró cuota para Over 2.5 goles")

    if cuota_btts:
        print(f"Cuota Ambos Anotan: {cuota_btts}")
    else:
        print("No se encontró cuota para Ambos Anotan")

# Fixture de prueba (reemplazar por fixture real activo)
if __name__ == "__main__":
    fixture_prueba = 123456  # Reemplazar con un fixture real
    analizar_fixture(fixture_prueba)
