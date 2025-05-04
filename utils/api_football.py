# Asegúrate de definir la función
def obtener_partidos_de_liga(liga_id, fecha, temporada):
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

# Y esta también si no está definida
def analizar_partido_futbol(partido, datos_estadisticos, cuotas):
    print(f"📊 Análisis dummy: {partido.get('fixture', {}).get('id')}")
    return {
        "pick": None,
        "valor": False,
        "motivo": "Análisis aún no implementado"
    }

