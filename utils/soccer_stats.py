def analyze_match(partido):
    return {
        "partido": partido.get("partido"),
        "liga": partido.get("liga"),
        "cuota": partido.get("cuota", 1.85),
        "stake": 1,
        "tipo": "ML",
        "equipo": partido.get("equipo_local"),
        "analisis": "Equipo local con buena forma y cuota justa.",
        "valor": True,
        "porcentaje_btts": 60,
        "prom_goles": 2.7,
        "prom_corners": 8.2,
        "prom_tarjetas": 4.0
    }

def get_soccer_matches(api_key, whitelist):
    return [
        {
            "partido": "Barcelona vs Sevilla",
            "equipo_local": "Barcelona",
            "equipo_visitante": "Sevilla",
            "liga": "La Liga",
            "cuota": 1.85
        },
        {
            "partido": "Arsenal vs Liverpool",
            "equipo_local": "Arsenal",
            "equipo_visitante": "Liverpool",
            "liga": "Premier League",
            "cuota": 2.00
        }
    ]
