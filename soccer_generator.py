from utils.api_football import obtener_partidos_de_liga, analizar_partido_futbol
from utils.soccer_utils import cargar_datos_estadisticos, cargar_cuotas
from utils.leagues import LEAGUES
from datetime import datetime
import time

def main():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    temporada_actual = 2024  # Puedes automatizar esto después

    print(f"📅 Fecha actual: {fecha_actual}")

    for liga in LEAGUES:
        liga_id = liga["league_id"]
        nombre_liga = liga["nombre"]

        print(f"🔎 Analizando {nombre_liga} - temporada {temporada_actual}")

        try:
            partidos = obtener_partidos_de_liga(liga_id, fecha=fecha_actual, temporada=temporada_actual)

            for partido in partidos:
                fixture_id = partido.get("fixture", {}).get("id")

                if not fixture_id:
                    continue

                datos_estadisticos = cargar_datos_estadisticos(fixture_id)
                cuotas = cargar_cuotas(fixture_id)

                resultado = analizar_partido_futbol(partido, datos_estadisticos, cuotas)

                print(f"📊 Análisis: {fixture_id}")
                print(f"📌 Resultado: {resultado}")

                time.sleep(1.2)  # Respeta límite de la API

        except Exception as e:
            print(f"❌ Error al analizar {nombre_liga}: {str(e)}")

if __name__ == "__main__":
    main()
