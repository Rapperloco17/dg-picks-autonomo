# utils/mlb_stats.py

def analizar_mlb(partido):
    # Análisis simulado para MLB
    equipo_local = partido['equipo_local']
    equipo_visitante = partido['equipo_visitante']
    cuota = partido['cuota']

    if "Yankees" in equipo_local or "Dodgers" in equipo_local:
        valor = True
        descripcion = f"{equipo_local} está en buena racha y tiene valor ante {equipo_visitante}."
    else:
        valor = False
        descripcion = f"No se detecta valor suficiente en el enfrentamiento {equipo_local} vs {equipo_visitante}."

    return {
        "valor": valor,
        "descripcion": descripcion,
        "cuota": cuota
    }
