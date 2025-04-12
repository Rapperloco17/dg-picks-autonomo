
# utils/soccer_stats.py

def obtener_partidos_futbol():
    return [
        {"equipo1": "Barcelona", "equipo2": "Real Madrid"},
        {"equipo1": "Tigres", "equipo2": "América"}
    ]

def analizar_equipo_futbol(partido):
    return {
        "descripcion": f"{partido['equipo1']} tiene mejor forma reciente y estadísticas ofensivas superiores."
    }
