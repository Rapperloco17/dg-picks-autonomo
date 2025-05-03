import requests
from utils.valor_cuota import calcular_valor_apuesta

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {
    "x-apisports-key": API_KEY
}


def obtener_partidos_de_liga(league_id, season):
    url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}&timezone=America/Mexico_City"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", [])
    else:
        return []


def analizar_partido_futbol(partido, datos_equipo_local, datos_equipo_visitante, prediccion, cuotas):
    # Lógica simple de análisis (ejemplo)
    analisis = {
        "partido_id": partido["fixture"]["id"],
        "equipos": f"{partido['teams']['home']['name']} vs {partido['teams']['away']['name']}",
        "prediccion": prediccion.get("winner", {}).get("name"),
        "valor_detectado": False,
        "cuota": cuotas.get("1", 0),
    }

    # Ejemplo de detección de valor
    if prediccion.get("winner", {}).get("name") == partido['teams']['home']['name'] and cuotas.get("1"):
        valor = calcular_valor_apuesta(0.55, cuotas.get("1"))  # Suponiendo 55% de probabilidad implícita
        analisis["valor_detectado"] = valor >= 1.05

    return analisis
