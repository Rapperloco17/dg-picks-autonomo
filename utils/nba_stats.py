# utils/nba_stats.py

def analizar_forma_nba(partido):
    equipo_local = partido['equipo_local']
    equipo_visitante = partido['equipo_visitante']
    cuota = partido['cuota']

    if "Lakers" in equipo_local or "Celtics" in equipo_local:
        valor = True
        descripcion = f"{equipo_local} está en buena forma y puede cubrir la línea contra {equipo_visitante}."
    else:
        valor = False
        descripcion = f"Partido parejo entre {equipo_local} y {equipo_visitante}, sin valor detectado."

    return {
        "valor": valor,
        "descripcion": descripcion,
        "cuota": cuota
    }
