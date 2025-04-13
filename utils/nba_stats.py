# utils/nba_stats.py

def obtener_partidos_nba():
    return [
        {"cuota": 1.90, "equipo_local": "Lakers", "equipo_visitante": "Warriors"},
        {"cuota": 2.20, "equipo_local": "Celtics", "equipo_visitante": "Heat"}
    ]

def analizar_forma_nba(partido):
    equipo_local = partido['equipo_local']
    equipo_visitante = partido['equipo_visitante']
    cuota = partido['cuota']

    if "Lakers" in equipo_local or "Celtics" in equipo_local:
        valor = True
        descripcion = f"{equipo_local} llega en buena forma. Opción de valor ante {equipo_visitante}."
    else:
        valor = False
        descripcion = f"{equipo_local} vs {equipo_visitante} parece más parejo. No hay valor claro."

    return {
        "valor": valor,
        "descripcion": descripcion,
        "cuota": cuota
    }

