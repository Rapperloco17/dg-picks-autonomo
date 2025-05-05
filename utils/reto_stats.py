# utils/reto_stats.py

def obtener_picks_reto():
    return [
        {"jugador1": "Jugador A", "jugador2": "Jugador B", "analisis": {"descripcion": "Valor en cuota y superioridad."}},
        {"jugador1": "Jugador C", "jugador2": "Jugador D", "analisis": {"descripcion": "Rendimiento estable en primeros sets."}}
    ]

def seleccionar_mas_seguro(picks):
    return picks[0] if picks else None

def seleccionar_paso(picks, paso):
    if len(picks) >= paso:
        return picks[paso - 1]
    return None

def guardar_pick_generado(pick):
    # Temporal: solo imprime el pick hasta que se defina el guardado real
    print(f"🔸 Pick generado (dummy): {pick['jugador1']} vs {pick['jugador2']}")
