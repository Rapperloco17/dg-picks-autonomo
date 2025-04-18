import os
import json
from datetime import datetime
from utils.api_football import get_fixtures_today, get_team_stats
from utils.valor_cuota import evaluar_valor_cuota

OUTPUT_FOLDER = "outputs"
LEAGUES_WHITELIST_PATH = "leagues_whitelist_ids.json"

def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def generate_soccer_picks():
    print("⚽ Iniciando generación de picks de fútbol...")

    whitelist = load_json(LEAGUES_WHITELIST_PATH)
    ligas_permitidas = whitelist.get("allowed_league_ids", [])

    fixtures = get_fixtures_today()
    partidos_validos = [
        f for f in fixtures
        if f.get("league_id") in ligas_permitidas
    ]

    print(f"📅 Partidos hoy en ligas permitidas: {len(partidos_validos)}")

    picks = []
    parlays = []

    for match in partidos_validos:
        stats = get_team_stats(match.get("fixture_id"), match.get("home_team_id"), match.get("away_team_id"))
        if not stats:
            continue

        cuota = stats["cuota"]
        mercado = stats["mercado"]
        probabilidad = stats["probabilidad"]
        btts = stats.get("btts")
        corners = stats.get("corners")
        tarjetas = stats.get("tarjetas")

        tiene_valor = evaluar_valor_cuota(probabilidad, cuota)

        pick = {
            "partido": f"{match.get('home_name')} vs {match.get('away_name')}",
            "cuota": cuota,
            "valor": True,
            "mercado": mercado,
            "liga": match.get("league_name"),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "stats": {
                "probabilidad": probabilidad,
                "btts": btts,
                "corners": corners,
                "tarjetas": tarjetas
            }
        }

        if tiene_valor:
            if 1.50 <= cuota <= 4.00:
                picks.append(pick)
            elif 1.30 <= cuota < 1.50:
                parlays.append(pick)

    print(f"✅ Picks individuales: {len(picks)} | Para parlays: {len(parlays)}")

    data = {
        "picks": picks,
        "parlays": parlays
    }

    nombre_archivo = f"futbol_{datetime.now().strftime('%Y-%m-%d')}.json"
    ruta_archivo = os.path.join(OUTPUT_FOLDER, nombre_archivo)
    save_json(data, ruta_archivo)
    print(f"📁 Picks guardados en {ruta_archivo}")

if __name__ == "__main__":
    generate_soccer_picks()
