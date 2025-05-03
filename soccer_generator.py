import os
import time
import json
from datetime import datetime
from utils.api_football import obtener_partidos_de_liga
from utils.leagues import cargar_ligas_permitidas
from utils.telegram import enviar_mensaje  # ✅ CORREGIDO

# ⚽ Configuración general
LIGAS_PERMITIDAS = cargar_ligas_permitidas()
FIXTURES_ANALIZADOS = []
PICKS_GENERADOS = []

# 📊 Análisis de un partido
from analysis.match_insights import analizar_partido_profundo  # Asegúrate de tener este import arriba

def analizar_partido(fixture):
    try:
        pick = analizar_partido_profundo(fixture)
        if pick:
            PICKS_GENERADOS.append(pick)
            enviar_mensaje(f"🎯 PICK DG Picks\n📌 {pick['pick']}\n🧠 {pick['razonamiento'][0]}")
        FIXTURES_ANALIZADOS.append(fixture)
    except Exception as e:
        print(f"⚠️ Error al analizar fixture {fixture['fixture']['id']}: {e}")


# 💾 Guardar fixtures analizados del día
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

# 🧹 Limpieza de archivos viejos
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
    print("⚽ Iniciando análisis DG Picks...\n")
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')

    for liga_id in LIGAS_PERMITIDAS:
        try:
            data = obtener_partidos_de_liga(int(liga_id), fecha_hoy)
            for fixture in data.get("response", []):
                analizar_partido(fixture)
        except Exception as e:
            print(f"❌ Error al analizar liga {liga_id}: {e}")

    guardar_fixture_diario()
    limpiar_historial_antiguo()

    print(f"\n✅ Proceso finalizado: {len(FIXTURES_ANALIZADOS)} partidos analizados | {len(PICKS_GENERADOS)} picks generados.")

