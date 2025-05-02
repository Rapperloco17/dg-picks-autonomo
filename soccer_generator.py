import os
import time
import json
from datetime import datetime
from utils.api_football import get_fixtures_today, get_match_stats, get_prediction
from utils.leagues import cargar_ligas_permitidas
from utils.telegram_bot import enviar_mensaje

# ⚽ Configuración general
LIGAS_PERMITIDAS = cargar_ligas_permitidas()
FIXTURES_ANALIZADOS = []
PICKS_GENERADOS = []

# 📊 Análisis de un partido
def analizar_partido(fixture):
    fixture_id = fixture['fixture']['id']
    equipos = fixture['teams']
    local = equipos['home']['name']
    visitante = equipos['away']['name']
    liga = fixture['league']['name']

    try:
        stats = get_match_stats(fixture_id)
        prediccion = get_prediction(fixture_id)

        goles_local = stats.get('goals_avg_home', 0)
        goles_visitante = stats.get('goals_avg_away', 0)

        analisis = {
            "id_fixture": fixture_id,
            "liga": liga,
            "equipos": f"{local} vs {visitante}",
            "goles_prom_local": goles_local,
            "goles_prom_visitante": goles_visitante,
            "prediccion_api": prediccion.get('winner'),
            "probabilidades": prediccion.get('percent'),
            "pick_generado": None
        }

        # 🎯 Lógica simple de generación de pick
        if goles_local + goles_visitante >= 2.8:
            pick = f"Over 2.5 goles en {local} vs {visitante}"
            cuota = 1.80  # Se puede traer de la API si está activa
            PICK = {
                "fixture_id": fixture_id,
                "pick": pick,
                "cuota": cuota
            }
            PICKS_GENERADOS.append(PICK)
            analisis["pick_generado"] = PICK

            # ✅ Envío al canal VIP (opcional: cambiar por revisión manual)
            enviar_mensaje(f"🎯 PICK DG Picks\n{pick}\nCuota: {cuota}\n✅ Valor detectado en estadísticas")

        FIXTURES_ANALIZADOS.append(analisis)

    except Exception as e:
        print(f"⚠️ Error al analizar fixture {fixture_id}: {e}")

# 💾 Guardar todos los fixtures analizados del día
def guardar_fixture_diario():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    carpeta = 'historial/fixtures'
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f'{fecha_hoy}.json')

    data = {
        'fecha': fecha_hoy,
        'total_partidos': len(FIXTURES_ANALIZADOS),
        'total_picks': len(PICKS_GENERADOS),
        'fixtures': FIXTURES_ANALIZADOS,
        'picks_generados': PICKS_GENERADOS
    }

    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f'✅ Análisis del día guardado en: {ruta}')

# 🧹 Limpieza automática del historial viejo
def limpiar_historial_antiguo(directorio='historial/fixtures', dias=15):
    ahora = time.time()
    if not os.path.exists(directorio):
        return
    for archivo in os.listdir(directorio):
        ruta = os.path.join(directorio, archivo)
        if os.path.isfile(ruta):
            tiempo_archivo = os.path.getmtime(ruta)
            if ahora - tiempo_archivo > dias * 86400:
                os.remove(ruta)
                print(f'🧹 Archivo viejo eliminado: {archivo}')

# 🏁 FLUJO PRINCIPAL
if __name__ == "__main__":
    print("⚽ Iniciando análisis diario de DG Picks...\n")

    fixtures = get_fixtures_today()

    for fixture in fixtures:
        liga_id = fixture['league']['id']
        if liga_id in LIGAS_PERMITIDAS:
            analizar_partido(fixture)

    guardar_fixture_diario()
    limpiar_historial_antiguo()

    print("\n✅ Proceso finalizado. Total analizados:", len(FIXTURES_ANALIZADOS), "| Picks generados:", len(PICKS_GENERADOS))
