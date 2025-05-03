
import json
import os
from datetime import datetime
from utils.api_football import obtener_partidos_de_liga, analizar_partido_futbol

def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Fecha actual: {fecha_hoy}")

    with open("utils/leagues_whitelist_ids.json", "r", encoding="utf-8") as f:
        ligas_validas = json.load(f)

    with open("utils/league_seasons.json", "r", encoding="utf-8") as f:
        temporadas_por_liga = json.load(f)

    all_picks = []

    for liga_id in ligas_validas.keys():
        temporada = temporadas_por_liga.get(str(liga_id), 2024)
        print(f"🔍 Analizando liga {liga_id} - temporada {temporada}")

        partidos = obtener_partidos_de_liga(liga_id, fecha_hoy, temporada)
        fixtures = partidos.get("response", [])
        print(f"➡️ Fixtures obtenidos: {len(fixtures)}")

        for fixture in fixtures:
            try:
                pick = analizar_partido_futbol(fixture)
                if pick:
                    print(f"✅ Pick generado: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} → {pick['pick']}")
                    all_picks.append(pick)
                else:
                    print(f"⛔ Sin pick válido para: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
            except Exception as e:
                print(f"❌ Error analizando fixture {fixture.get('fixture', {}).get('id')}: {e}")

    os.makedirs("output", exist_ok=True)
    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(all_picks, f, indent=4, ensure_ascii=False)

    print(f"🎯 Total de picks generados: {len(all_picks)}")

if __name__ == "__main__":
    main()
