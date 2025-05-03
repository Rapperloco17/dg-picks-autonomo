# utils/api_football.py

def obtener_partidos_de_liga(liga_id, fecha_hoy, temporada):
    # Simula una respuesta directa como lista para pruebas (puedes reemplazar por lógica real con requests)
    partidos = [
        {
            "fixture": {"id": 12345, "date": fecha_hoy},
            "teams": {"home": {"name": "Equipo A"}, "away": {"name": "Equipo B"}},
            "league": {"id": liga_id, "season": temporada}
        }
    ]
    return partidos

def analizar_partido_futbol(partido, datos_estadisticos, cuotas):
    """
    Función dummy temporal para evitar crash del sistema.
    Retorna None para cada análisis, sin procesar lógica real.

    :param partido: dict con datos del fixture
    :param datos_estadisticos: dict con estadísticas del partido
    :param cuotas: dict con cuotas disponibles
    :return: dict o None
    """
    # Esta función será reemplazada por el análisis real más adelante.
    return None
