
# utils/sofascore.py

def obtener_partidos_tenis():
    # Simulación de partidos obtenidos desde SofaScore
    return [
        {"jugador1": "Jugador A", "jugador2": "Jugador B"},
        {"jugador1": "Jugador C", "jugador2": "Jugador D"}
    ]

def analizar_rompimientos(partido):
    # Análisis simulado de probabilidad de rompimiento en el primer set
    return {
        "jugador1_rompe": True,
        "jugador2_rompe": False,
        "descripcion": f"{partido['jugador1']} tiene buen desempeño al resto. {partido['jugador2']} vulnerable en su primer servicio."
    }
