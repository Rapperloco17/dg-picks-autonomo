
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
    return {
        "ganador": pred.get("winner", {}).get("name"),
        "btts": pred.get("both_teams_to_score", {}).get("yes"),
        "over25": pred.get("goals", {}).get("over_2_5", {}).get("percentage")
    }

def obtener_h2h(local_id, visitante_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={local_id}-{visitante_id}&last=5"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    data = response.json().get("response", [])
    return [f"{p.get('goals', {}).get('home', 0)}-{p.get('goals', {}).get('away', 0)}" for p in data]

def obtener_cuotas(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=6"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
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
    return cuotas

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

    corners_l = forma_local.get("corners", {}).get("total", {}).get("total", 0)
    corners_v = forma_visitante.get("corners", {}).get("total", {}).get("total", 0)
    tarjetas_l = forma_local.get("cards", {}).get("yellow", {}).get("total", 0)
    tarjetas_v = forma_visitante.get("cards", {}).get("yellow", {}).get("total", 0)

    predicciones = obtener_predicciones(partido["fixture_id"])
    cuotas = obtener_cuotas(partido["fixture_id"])
    h2h = obtener_h2h(partido["local_id"], partido["visitante_id"])

    print(f"\n🔍 {partido['local']} vs {partido['visitante']} ({partido['liga']})")
    print(f"  🏠 {partido['local']}: Forma: {forma_l} | Goles Casa: {prom_gf_l:.1f} / Contra: {prom_gc_l:.1f}, Corners: {corners_l}, Amarillas: {tarjetas_l}")
    print(f"  🚶‍♂️ {partido['visitante']}: Forma: {forma_v} | Goles Visita: {prom_gf_v:.1f} / Contra: {prom_gc_v:.1f}, Corners: {corners_v}, Amarillas: {tarjetas_v}")
    print(f"  📊 Predicción: Gana {predicciones.get('ganador', 'N/D')} | BTTS: {predicciones.get('btts', 'N/D')} | Over 2.5: {predicciones.get('over25', 'N/D')}%")
    if h2h:
        print(f"  🆚 Últimos H2H: {' | '.join(h2h)}")
    print(f"  💸 Cuotas: ML Local {cuotas.get('local', '-')}, Empate {cuotas.get('empate', '-')}, Visitante {cuotas.get('visitante', '-')}, BTTS Sí {cuotas.get('btts', '-')}, Over 2.5 {cuotas.get('over_2_5', '-')}")

    recomendaciones = []
    if predicciones.get("over25") and predicciones["over25"].isdigit() and int(predicciones["over25"]) >= UMBRAL_GOLES and "over_2_5" in cuotas:
        recomendaciones.append(f"✅ Pick sugerido: Over 2.5 goles @ {cuotas['over_2_5']}")
    if predicciones.get("btts") and predicciones["btts"].isdigit() and int(predicciones["btts"]) >= UMBRAL_BTTS and "btts" in cuotas:
        recomendaciones.append(f"✅ Pick sugerido: Ambos anotan (BTTS) @ {cuotas['btts']}")
    if (corners_l + corners_v) / 2 >= UMBRAL_CORNERS:
        recomendaciones.append(f"⚠️ Pick sugerido: Over en corners (media: {(corners_l + corners_v)/2:.1f})")
    if (tarjetas_l + tarjetas_v) / 2 >= UMBRAL_TARJETAS:
        recomendaciones.append(f"⚠️ Pick sugerido: Over en tarjetas (media: {(tarjetas_l + tarjetas_v)/2:.1f})")

    print(f"\n🎯 Promedio total de corners: {(corners_l + corners_v) / 2:.1f}")
    print(f"🎯 Promedio total de tarjetas: {(tarjetas_l + tarjetas_v) / 2:.1f}")

    if recomendaciones:
        print("\n🔐 Recomendaciones:")
        for r in recomendaciones:
            print("   -", r)
    else:
        print("🔎 Sin recomendaciones claras para este partido.")

def main():
    print(f"\n📅 Análisis de partidos del día {FECHA_HOY}")
    partidos = obtener_fixtures_del_dia()
    for partido in partidos:
        analizar_partido(partido)

if __name__ == "__main__":
    main()
