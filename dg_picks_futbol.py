import json
from datetime import datetime
from utils.api_football import obtener_partidos_de_liga, obtener_estadisticas_fixture, obtener_prediccion_fixture, obtener_cuotas_fixture
from utils.leagues_whitelist import leagues_ids

print("🔍 Buscando partidos del día...")

fecha_hoy = datetime.utcnow().strftime("%Y-%m-%d")

partidos_del_dia = []

for league_id in leagues_ids:
    try:
        partidos = obtener_partidos_de_liga(league_id, fecha_hoy, 2024)
        partidos_del_dia.extend(partidos)
    except Exception as e:
        print(f"❌ Error al obtener partidos de liga {league_id}: {e}")

print(f"✅ Se encontraron {len(partidos_del_dia)} partidos en {len(leagues_ids)} ligas autorizadas")

picks_generados = []

for partido in partidos_del_dia:
    try:
        fixture_id = partido["fixture"]["id"]
        nombre_partido = f"{partido['teams']['home']['name']} vs {partido['teams']['away']['name']}"
        print(f"\n⚽ Partido: {nombre_partido}")

        cuotas = obtener_cuotas_fixture(fixture_id, "1x2")
        prediccion = obtener_prediccion_fixture(fixture_id)
        stats = obtener_estadisticas_fixture(fixture_id)

        prediccion_equipo = prediccion.get("winner", {}).get("name", "-")
        print(f"🔮 Predicción API: {prediccion_equipo}")

        print("📊 Estadísticas:")
        print("- promedio_goles:", stats.get("promedio_goles"))
        print("- prob_btts:", stats.get("prob_btts"))
        print("- forma_local:", stats.get("forma_local"))
        print("- forma_visitante:", stats.get("forma_visitante"))
        print("- tarjetas:", stats.get("tarjetas"))
        print("- corners:", stats.get("corners"))

        print("💸 Cuotas:")
        for key, value in cuotas.items():
            print(f"- {key}: {value}")

        # Ejemplo básico de lógica
        if stats.get("promedio_goles", 0) > 3 and cuotas.get("over_2.5", 0) >= 1.70:
            pick = {
                "partido": nombre_partido,
                "pick": "Over 2.5 goles",
                "cuota": cuotas.get("over_2.5"),
                "motivo": "Promedio alto de goles y cuota aceptable",
                "fecha_generacion": datetime.utcnow().isoformat()
            }
            picks_generados.append(pick)
            print("✅ Pick generado con valor")
        else:
            print("❌ No se generó pick con valor")

    except Exception as e:
        print(f"❌ Error en fixture {fixture_id}: {e}")

with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
    json.dump(picks_generados, f, indent=2, ensure_ascii=False)

print("\n📥 Análisis finalizado. Picks guardados en output/picks_futbol.json")
