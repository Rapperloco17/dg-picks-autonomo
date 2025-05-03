import json
from datetime import datetime
from utils.api_futbol import obtener_partidos_de_liga, get_team_statistics, get_predictions
from utils.leagues_whitelist_ids import ligas_validas
from analysis.match_insights import analizar_partido_profundo
import os


# Fecha actual para analizar partidos del día
fecha_actual = datetime.now().strftime("%Y-%m-%d")

# Lista para almacenar todos los partidos
fixtures = []

# Obtener todos los fixtures de cada liga autorizada
for liga_id in ligas_validas:
    partidos_liga = obtener_partidos_de_liga(liga_id, fecha_actual)
    fixtures.extend(partidos_liga)

# Contadores
analizados = 0
picks_generados = []

# Procesar cada fixture con datos completos
for fixture in fixtures:
    fixture_id = fixture['fixture']['id']

    stats = get_team_statistics(fixture_id)
    prediction = get_predictions(fixture_id)

    # Validar datos antes de analizar
    if not stats or not isinstance(stats, dict) or not prediction or not isinstance(prediction, dict):
        print(f"⚠️ No se pudieron obtener datos para fixture {fixture_id}")
        continue

    try:
        analisis = analizar_partido_profundo(fixture, stats, prediction)
        if analisis:
            analizados += 1
            picks_generados.append(analisis)
    except Exception as e:
        print(f"❌ Error en análisis profundo del fixture {fixture_id}: {e}")

# Guardar resultados en archivo JSON con fecha
nombre_archivo = f"historial/fixtures/{datetime.now().strftime('%Y-%m-%d')}.json"
os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)
with open(nombre_archivo, "w", encoding="utf-8") as f:
    json.dump(picks_generados, f, indent=2, ensure_ascii=False)

print(f"✅ Análisis del día guardado en: {nombre_archivo}")
print(f"📊 Proceso finalizado: {analizados} partidos analizados | {len(picks_generados)} picks generados.")
