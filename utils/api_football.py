from utils.analizar_partido_futbol import analizar_partido_futbol

def obtener_partidos_de_liga(liga_id, fecha, temporada):
    # Dummy para pruebas mientras se implementa el consumo real de la API
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


def analizar_partido_dummy(partido, datos_estadisticos, cuotas):
    print(f"📊 Análisis dummy: {partido.get('fixture', {}).get('id')}")
    return {
        "pick": None,
        "valor": False,
        "motivo": "Análisis aún no implementado"
    }
