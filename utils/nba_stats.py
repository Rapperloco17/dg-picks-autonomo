
# utils/nba_stats.py

def obtener_partidos_nba():
    return [
        {"equipo1": "Lakers", "equipo2": "Warriors"},
        {"equipo1": "Bucks", "equipo2": "Celtics"}
    ]

def analizar_informacion_jugadores(partido):
    return {
        "descripcion": f"{partido['equipo1']} llega más descansado, con ventaja estadística en rebotes y defensa."
    }
