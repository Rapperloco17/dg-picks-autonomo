def obtener_partidos_de_liga(liga_id, fecha, temporada):
    # Función dummy con simulación de fixtures para evitar crash
    print(f"Dummy activa - obtener_partidos_de_liga(liga_id={liga_id}, fecha={fecha}, temporada={temporada})")

    partidos_simulados = [
        {
            "fixture": {"id": 12345, "date": fecha},
            "teams": {
                "home": {"name": "Equipo Local"},
                "away": {"name": "Equipo Visitante"}
            },
            "league": {"id": liga_id, "season": temporada}
        }
    ]
    return partidos_simulados


def analizar_partido_futbol(partido, datos_estadisticos, cuotas):
    # Función dummy para evitar crash mientras se completa la lógica
    print(f"Análisis dummy: {partido.get('fixture', {}).get('id')}")
    return {
        "pick": None,
        "valor": False,
        "motivo": "Análisis aún no implementado"
    }
