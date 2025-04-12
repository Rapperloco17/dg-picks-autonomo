def obtener_partidos_tenis():
    return [
        {"cuota": 1.75, "jugador_1": "Djokovic", "jugador_2": "Alcaraz"},
        {"cuota": 2.10, "jugador_1": "Medvedev", "jugador_2": "Tsitsipas"}
    ]

def obtener_partidos_mlb():
    return [
        {"cuota": 1.85, "equipo_local": "Yankees", "equipo_visitante": "Red Sox"},
        {"cuota": 2.05, "equipo_local": "Dodgers", "equipo_visitante": "Giants"}
    ]

def obtener_partidos_nba():
    return [
        {"cuota": 1.90, "equipo_local": "Lakers", "equipo_visitante": "Warriors"},
        {"cuota": 2.20, "equipo_local": "Celtics", "equipo_visitante": "Heat"}
    ]

def obtener_partidos_futbol():
    return [
        {"cuota": 1.95, "equipo_local": "Real Madrid", "equipo_visitante": "Barcelona"},
        {"cuota": 2.30, "equipo_local": "Arsenal", "equipo_visitante": "Liverpool"}
    ]

def analizar_rompimientos(partido):
    return {
        "jugador1_rompe": True,
        "jugador2_rompe": False,
        "descripcion": f"{partido['jugador_1']} tiene buen desempeño al resto. {partido['jugador_2']} vulnerable en su primer servicio."
    }
