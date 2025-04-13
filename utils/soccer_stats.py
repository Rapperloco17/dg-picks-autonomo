# utils/soccer_stats.py

def analizar_forma_futbol(partido):
    equipo_local = partido['equipo_local']
    equipo_visitante = partido['equipo_visitante']
    cuota = partido['cuota']

    if "Real Madrid" in equipo_local or "Arsenal" in equipo_local:
        valor = True
        descripcion = f"{equipo_local} ha mostrado solidez en casa. Buena opción frente a {equipo_visitante}."
    else:
        valor = False
        descripcion = f"Partido equilibrado entre {equipo_local} y {equipo_visitante}. No se detecta valor claro."

    return {
        "valor": valor,
        "descripcion": descripcion,
        "cuota": cuota
    }
