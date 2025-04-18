import requests
import time

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}


def buscar_fixture_local(equipo1, equipo2, fecha):
    url = f"{BASE_URL}/fixtures"
    params = {
        "date": fecha,
        "timezone": "America/Mexico_City"
    }
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        if data["response"]:
            for item in data["response"]:
                t1 = item["teams"]["home"]["name"].lower()
                t2 = item["teams"]["away"]["name"].lower()
                if equipo1.lower() in t1 and equipo2.lower() in t2 or equipo1.lower() in t2 and equipo2.lower() in t1:
                    return item
    except Exception as e:
        print("Error buscando fixture:", e)
    return None


def obtener_resultado_partido(pick):
    fecha = pick.get("fecha")
    equipos = pick.get("partido", "vs").split(" vs ")
    if len(equipos) != 2:
        return None

    equipo1 = equipos[0].strip()
    equipo2 = equipos[1].strip()

    fixture = buscar_fixture_local(equipo1, equipo2, fecha)
    if not fixture:
        return None

    resultado = {
        "goles_local": fixture["goals"]["home"],
        "goles_visita": fixture["goals"]["away"],
        "nombre_local": fixture["teams"]["home"]["name"],
        "nombre_visita": fixture["teams"]["away"]["name"],
        "tarjetas": fixture.get("statistics", []),
        "fixture_id": fixture["fixture"]["id"]
    }
    return resultado


if __name__ == "__main__":
    ej = {
        "partido": "Arsenal vs Chelsea",
        "fecha": "2025-04-15"
    }
    print(obtener_resultado_partido(ej))
