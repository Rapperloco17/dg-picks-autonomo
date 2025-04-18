import os
import json
from datetime import datetime
from utils.api_football import get_fixtures_today, get_team_stats
from utils.valor_cuota import evaluar_valor_cuota

OUTPUT_FOLDER = "outputs/"
LEAGUES_WHITELIST_PATH = "leagues_whitelist.json"

def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def generate_soccer_picks():
    print("🔍 Iniciando generación de picks de fútbol...")

    whitelist = load_json(LEAGUES_WHITELIST_PATH)
    ligas_autorizadas = whitelist.get("ligas", [])

    fixtures = get_fixtures_today()
    partidos_validos = [
        f for f in fixtures
        if f.get("league_name") in ligas_autorizadas
    ]

    print(f"📅 Partidos hoy en ligas permitidas: {len(partidos_validos)}")

    picks = []

    for match in partidos_validos:
        stats = get_team_stats(match["fixture_id"], match["home_team_id"], match["away_team_id"])
        if not stats:
            continue

        # Análisis: Over 2.5 goles
        prob_over25 = stats.get("over_2_5", 0)
        btts = stats.get("btts", 0)
        corners = stats.get("prom_corners", 0)
        tarjetas = stats.get("prom_tarjetas", 0)
        cuota = match.get("cuota_over25", 1.80)

        tiene_valor = evaluar_valor_cuota(prob_over25, cuota)

        if tiene_valor:
            pick = {
                "partido": f'{match["home_team"]} vs {match["away_team"]}',
                "cuota": cuota,
                "valor": True,
                "mercado": "Over 2.5 goles",
                "liga": match["league_name"],
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "stats": {
                    "prob_over25": prob_over25,
                    "btts": btts,
                    "corners": corners,
                    "tarjetas": tarjetas
                }
            }
            picks.append(pick)

    print(f"✅ Picks generados: {len(picks)}")

    data = {"picks": picks}
    nombre_archivo = f"futbol_{datetime.now().strftime('%Y-%m-%d')}.json"
    ruta_archivo = os.path.join(OUTPUT_FOLDER, nombre_archivo)
    save_json(data, ruta_archivo)
    print(f"💾 Picks guardados en {ruta_archivo}")

if __name__ == "__main__":
    generate_soccer_picks()
