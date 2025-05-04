from utils.partidos_disponibles import obtener_partidos_disponibles
from utils.api_football import obtener_datos_partido, obtener_estadisticas_partido, obtener_cuotas_partido
from utils.analizar_partido_futbol import analizar_partido_futbol
from datetime import datetime

def main():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    print(f"\n📅 Fecha actual: {fecha_actual}")

    partidos = obtener_partidos_disponibles()

    if not partidos:
        print("⚠️ No hay partidos disponibles para analizar hoy.")
        return

    for p in partidos:
        fixture_id = p.get("fixture", {}).get("id")
        if not fixture_id:
            continue

        print(f"\n🔍 Analizando fixture {fixture_id}")

        try:
            datos = obtener_datos_partido(fixture_id)
            stats = obtener_estadisticas_partido(fixture_id)
            cuotas = obtener_cuotas_partido(fixture_id)

            resultado = analizar_partido_futbol(datos, stats, cuotas)

            if resultado:
                print(f"✅ Pick generado: {resultado}")
            else:
                print("❌ No se encontró valor en este partido.")

        except Exception as e:
            print(f"❌ Error en el análisis del fixture {fixture_id}: {e}")

if __name__ == "__main__":
    main()


