def obtener_partidos_de_liga(league_id, fecha, temporada):
    """
    Función simulada que retorna estructura esperada por soccer_generator.py.
    Retorna un diccionario con clave 'response' que contiene una lista de partidos.

    :param league_id: ID de la liga
    :param fecha: Fecha de consulta (YYYY-MM-DD)
    :param temporada: Año de la temporada (ej. 2024)
    :return: dict con clave 'response' y lista de fixtures simulados
    """
    return {
        "response": [
            {
                "fixture": {"id": 1, "date": fecha},
                "teams": {
                    "home": {"name": "Equipo A"},
                    "away": {"name": "Equipo B"}
                },
                "goals": {"home": 2, "away": 1},
                "league": {"id": league_id, "season": temporada}
            }
        ]
    }
