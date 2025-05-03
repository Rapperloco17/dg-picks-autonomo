def analizar_partido_futbol(partido, datos_estadisticos=None, cuotas=None):
    """
    Genera un pick simulado básico para testeo.

    :param partido: dict con datos del fixture
    :param datos_estadisticos: opcional (no usado en dummy)
    :param cuotas: opcional (no usado en dummy)
    :return: dict con pick simulado
    """
    local = partido["teams"]["home"]["name"]
    visitante = partido["teams"]["away"]["name"]
    fecha = partido["fixture"]["date"]

    return {
        "partido": f"{local} vs {visitante}",
        "fecha": fecha,
        "pick": f"{local} gana o empata",
        "mercado": "Doble Oportunidad",
        "cuota": 1.65,
        "confianza": "media",
        "justificacion": f"{local} juega en casa y llega con buena forma. Pick simulado."
    }
