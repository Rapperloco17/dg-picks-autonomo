# soccer_generator.py

from utils.partidos_disponibles import obtener_partidos_disponibles
from utils.api_football import obtener_datos_partido, obtener_estadisticas_partido, obtener_cuotas_partido
from utils.analizar_partido_futbol import analizar_partido_futbol
from datetime import datetime

def main():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Fecha actual: {fecha_actual}")
    
    partidos = obtener_partidos_disponibles(fecha_actual)
    
    if not partidos:
        print("⚠️ No hay partidos disponibles para analizar.")
        return

    for p in partidos:
        liga_id = p["liga_id"]
        fixture_id = p["fixture_id"]
        temporada = p["temporada"]

        print(f"\n🔍 Analizando fixture {fixture_id} | Liga {liga_id} - temporada {temporada}")

        try:
            datos = obtener_datos_partido(fixture_id)
            stats = obtener_estadisticas_partido(fixture_id)
            cuotas = obtener_cuotas_partido(fixture_id)

            resultado = analizar_partido_futbol(datos, stats, cuotas)

            print(f"✅ Resultado: {resultado}")
        
        except Exception as e:
            print(f"❌ Error al analizar fixture {fixture_id}: {str(e)}")


if __name__ == "__main__":
    main()

