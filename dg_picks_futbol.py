
import requests
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

UMBRAL_GOLES = 65
UMBRAL_BTTS = 60
UMBRAL_CORNERS = 9
UMBRAL_TARJETAS = 4

LIGAS_VALIDAS_IDS = {
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73,
    45, 78, 79, 88, 94, 103, 106, 113, 119, 128, 129, 130,
    135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172,
    179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253,
    257, 262, 263, 265, 268, 271, 281, 345, 357
}

def obtener_fixtures_del_dia():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    partidos = []

    total = 0
    filtrados = 0

    for item in data.get("response", []):
        total += 1
        liga_id = item["league"]["id"]
        if liga_id not in LIGAS_VALIDAS_IDS:
            continue
        filtrados += 1
        partidos.append({
            "fixture_id": item["fixture"]["id"],
            "liga": item["league"]["name"],
            "liga_id": liga_id,
            "local": item["teams"]["home"]["name"],
            "visitante": item["teams"]["away"]["name"],
            "local_id": item["teams"]["home"]["id"],
            "visitante_id": item["teams"]["away"]["id"],
            "hora": item["fixture"]["date"]
        })

    print(f"\n📊 Total partidos recibidos: {total}")
    print(f"✅ Partidos en ligas válidas: {filtrados}")
    return partidos

def obtener_forma_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&season=2024&league={league_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    return response.json().get("response", {})

def obtener_predicciones(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
    data = response.json().get("response", [])
    if not data:
        return {}

    pred = data[0].get("predictions", {})
    goles = data[0].get("goals", {})

    return {
        "ganador": pred.get("winner", {}).get("name"),
        "btts_yes": pred.get("both_teams_to_score", {}).get("yes"),
        "btts_no": pred.get("both_teams_to_score", {}).get("no"),
        "over25": pred.get("goals", {}).get("over_2_5", {}).get("percentage"),
        "goles_home": goles.get("home"),
        "goles_away": goles.get("away")
    }

def obtener_h2h(local_id, visitante_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={local_id}-{visitante_id}&last=5"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    data = response.json().get("response", [])
    return [f"{p.get('goals', {}).get('home', 0)}-{p.get('goals', {}).get('away', 0)}" for p in data]


def obtener_cuotas(fixture_id):
    bookmaker_ids = [6, 1, 8, 9]  # Bet365, 1xBet, Pinnacle, William Hill
    for bookmaker_id in bookmaker_ids:
        url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker={bookmaker_id}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            continue
        data = response.json().get("response", [])
        cuotas = {}
        for mercado in data:
            for book in mercado.get("bookmakers", []):
                for tipo in book.get("bets", []):
                    if tipo["name"] == "Over/Under 2.5 goals":
                        for val in tipo.get("values", []):
                            if val["value"] == "Over 2.5":
                                cuotas["over_2_5"] = val["odd"]
                    if tipo["name"] == "Both Teams To Score":
                        for val in tipo.get("values", []):
                            if val["value"] == "Yes":
                                cuotas["btts"] = val["odd"]
                    if tipo["name"] == "Match Winner":
                        for val in tipo.get("values", []):
                            if val["value"] == "Home":
                                cuotas["local"] = val["odd"]
                            elif val["value"] == "Draw":
                                cuotas["empate"] = val["odd"]
                            elif val["value"] == "Away":
                                cuotas["visitante"] = val["odd"]
        if cuotas:
            return cuotas
    return {}


def analizar_partido(partido):
    forma_local = obtener_forma_equipo(partido["local_id"], partido["liga_id"])
    forma_visitante = obtener_forma_equipo(partido["visitante_id"], partido["liga_id"])
    if not forma_local or not forma_visitante:
        print("❌ Datos incompletos. Se omite este partido.")
        return

    def procesar_forma(cadena):
        ultimos = cadena[-5:] if cadena else ""
        return f"{' '.join(ultimos)} | {ultimos.count('W')}V – {ultimos.count('D')}E – {ultimos.count('L')}D"

    forma_l = procesar_forma(forma_local.get("form", ""))
    forma_v = procesar_forma(forma_visitante.get("form", ""))

    prom_gf_l = float(forma_local.get("goals", {}).get("for", {}).get("average", {}).get("home") or 0)
    prom_gc_l = float(forma_local.get("goals", {}).get("against", {}).get("average", {}).get("home") or 0)
    prom_gf_v = float(forma_visitante.get("goals", {}).get("for", {}).get("average", {}).get("away") or 0)
    prom_gc_v = float(forma_visitante.get("goals", {}).get("against", {}).get("average", {}).get("away") or 0)

    corners_l = forma_local.get("corners", {}).get("total", {}).get("total")
    corners_v = forma_visitante.get("corners", {}).get("total", {}).get("total")
    tarjetas_l = forma_local.get("cards", {}).get("yellow", {}).get("total")
    tarjetas_v = forma_visitante.get("cards", {}).get("yellow", {}).get("total")

    corners_total = "No disponible" if corners_l is None or corners_v is None else (corners_l + corners_v) / 2
    tarjetas_total = "No disponible" if tarjetas_l is None or tarjetas_v is None else (tarjetas_l + tarjetas_v) / 2

    pred = obtener_predicciones(partido["fixture_id"])
    cuotas = obtener_cuotas(partido["fixture_id"])
    h2h = obtener_h2h(partido["local_id"], partido["visitante_id"])

    print(f"\n🔍 {partido['local']} vs {partido['visitante']} ({partido['liga']})")
    print(f"  🏠 {partido['local']}: Forma: {forma_l} | GF: {prom_gf_l:.1f}, GC: {prom_gc_l:.1f}")
    print(f"  🚶‍♂️ {partido['visitante']}: Forma: {forma_v} | GF: {prom_gf_v:.1f}, GC: {prom_gc_v:.1f}")
    print(f"  📊 Predicción: Gana {pred.get('ganador', 'N/D')}, BTTS Sí: {pred.get('btts_yes', '—')}%, Over 2.5: {pred.get('over25', '—')}%")
    print(f"  🎯 Marcador tentativo: {pred.get('goles_home', '?')} - {pred.get('goles_away', '?')}")

    promedio_goles = (prom_gf_l + prom_gf_v)
    if not pred.get("over25"):
        if promedio_goles >= 3:
            print(f"  ⚠️ Estimación por promedio: OVER 2.5 probable (Promedio GF: {promedio_goles:.1f})")
        elif promedio_goles <= 2:
            print(f"  ⚠️ Estimación por promedio: UNDER 2.5 probable (Promedio GF: {promedio_goles:.1f})")

    if h2h:
        print(f"  🆚 Últimos H2H: {' | '.join(h2h)}")

    print(f"  💸 Cuotas: ML Local {cuotas.get('local', '-')}, Empate {cuotas.get('empate', '-')}, Visitante {cuotas.get('visitante', '-')}, BTTS Sí {cuotas.get('btts', '-')}, Over 2.5 {cuotas.get('over_2_5', '-')}")
    print(f"  📉 Promedio total de corners: {corners_total}")
    print(f"  📉 Promedio total de tarjetas: {tarjetas_total}")

def main():
    print(f"\n📅 Análisis de partidos del día {FECHA_HOY}")
    partidos = obtener_fixtures_del_dia()
    for partido in partidos:
        analizar_partido(partido)

if __name__ == "__main__":
    main()
