from utils.api_football import obtener_partidos_de_liga, analizar_partido_futbol
from datetime import datetime

def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Fecha actual: {fecha_hoy}")

    # Ligas de ejemplo (puedes cargar desde JSON real después)
    ligas = [
        {"league_id": 2, "nombre": "liga 2", "temporada": 2024},
        {"league_id": 3, "nombre": "liga 3", "temporada": 2024},
    ]

    for liga in ligas:
        liga_id = liga["league_id"]
        temporada = liga["temporada"]
        nombre = liga["nombre"]

        print(f"⚽ Analizando {nombre} - temporada {temporada}")

        try:
            partidos = obtener_partidos_de_liga(liga_id=liga_id, fecha=fecha_hoy, temporada=temporada)

            # Compatibilidad con dummy y real
            fixtures = partidos.get("response", []) if isinstance(partidos, dict) else partidos

            for partido in fixtures:
                resultado = analizar_partido_futbol(partido, {}, {})
                if resultado:
                    print(f"📊 Resultado: {resultado}")
        except Exception as e:
            print(f"❌ Error analizando {nombre}: {e}")

if __name__ == "__main__":
    main()
