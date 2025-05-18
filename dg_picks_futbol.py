
import requests
import json
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

LIGAS_VALIDAS = [
    1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13,
    78, 79, 80, 82, 88, 94, 135, 136, 137, 140,
    141, 143, 144, 145, 146, 147, 148, 149, 165,
    168, 169, 170, 203, 207, 208, 210, 211, 212,
    213, 214, 235, 253, 256, 262, 268, 270, 271
]

def get_fixtures_hoy():
    hoy = datetime.today().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get('response', [])

def get_stats_por_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    r = requests.get(url, headers=HEADERS)
    return r.json().get("response", {})

def get_cuotas_por_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=6"
    r = requests.get(url, headers=HEADERS)
    return r.json().get("response", [])

def redondear_marcador(gf_local, gc_vis, gf_vis, gc_local):
    est_local = (gf_local + gc_vis) / 2
    est_vis = (gf_vis + gc_local) / 2
    return round(est_local), round(est_vis)

def extraer_cuotas(data):
    cuotas = {"local": "-", "empate": "-", "visitante": "-", "over_2_5": "-", "btts": "-"}
    for mercado in data:
        for apuesta in mercado.get("bookmakers", []):
            for tipo in apuesta.get("bets", []):
                if tipo["name"] == "Match Winner":
                    for val in tipo["values"]:
                        if val["value"] == "Home":
                            cuotas["local"] = val["odd"]
                        elif val["value"] == "Draw":
                            cuotas["empate"] = val["odd"]
                        elif val["value"] == "Away":
                            cuotas["visitante"] = val["odd"]
                elif tipo["name"] == "Over/Under 2.5 goals":
                    for val in tipo["values"]:
                        if val["value"] == "Over 2.5":
                            cuotas["over_2_5"] = val["odd"]
                elif tipo["name"] == "Both Teams To Score":
                    for val in tipo["values"]:
                        if val["value"] == "Yes":
                            cuotas["btts"] = val["odd"]
    return cuotas

def analizar_fixture(fixture):
    fixture_id = fixture["fixture"]["id"]
    liga_id = fixture["league"]["id"]
    if liga_id not in LIGAS_VALIDAS:
        return

    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]

    stats_home = get_stats_por_equipo(home["id"], liga_id)
    stats_away = get_stats_por_equipo(away["id"], liga_id)

    if not stats_home or not stats_away:
        return

    gf_home = stats_home["goals"]["for"]["average"]["total"]
    gc_home = stats_home["goals"]["against"]["average"]["total"]
    gf_away = stats_away["goals"]["for"]["average"]["total"]
    gc_away = stats_away["goals"]["against"]["average"]["total"]

    marcador_home, marcador_away = redondear_marcador(gf_home, gc_away, gf_away, gc_home)

    cuotas_raw = get_cuotas_por_fixture(fixture_id)
    cuotas = extraer_cuotas(cuotas_raw)

    print(f"📊 {home['name']} vs {away['name']} ({fixture['league']['name']})")
    print(f"🧠 ML: {home['name']} ({cuotas['local']}) – Empate ({cuotas['empate']}) – {away['name']} ({cuotas['visitante']})")
    print(f"🔢 Marcador tentativo: {marcador_home} – {marcador_away}")
    print(f"🔥 Cuotas: Over 2.5: {cuotas['over_2_5']} | BTTS Sí: {cuotas['btts']}")
    print("")

def main():
    print(f"📅 Análisis de partidos del día {datetime.today().strftime('%Y-%m-%d')}")
    fixtures = get_fixtures_hoy()
    print(f"⭐ Total partidos encontrados: {len(fixtures)}")
    for fixture in fixtures:
        analizar_fixture(fixture)

if __name__ == "__main__":
    main()
