def analizar_partido_futbol(partido, datos_estadisticos, cuotas):
    """
    Análisis inicial simple basado en estadísticas recientes y goles promedio.
    Devuelve pick si hay valor detectado en Over/Under o BTTS.
    """
    try:
        equipo_local = partido["teams"]["home"]["name"]
        equipo_visitante = partido["teams"]["away"]["name"]

        stats_local = datos_estadisticos.get("local", {})
        stats_visitante = datos_estadisticos.get("visitante", {})

        # Goles promedio
        goles_local = stats_local.get("goles_promedio", 0)
        goles_visitante = stats_visitante.get("goles_promedio", 0)
        total_goles = goles_local + goles_visitante

        # Forma reciente
        forma_local = stats_local.get("forma", [])
        forma_visitante = stats_visitante.get("forma", [])

        btts_local = stats_local.get("btts", 0)
        btts_visitante = stats_visitante.get("btts", 0)

        # Reglas básicas para detección de valor
        if total_goles >= 2.8 and cuotas.get("over_2.5", 0) >= 1.75:
            return {
                "pick": f"Más de 2.5 goles en {equipo_local} vs {equipo_visitante}",
                "valor": True,
                "motivo": f"Promedio de goles alto: {total_goles:.2f} entre ambos equipos",
                "cuota": cuotas["over_2.5"]
            }

        if btts_local >= 0.6 and btts_visitante >= 0.6 and cuotas.get("btts", 0) >= 1.80:
            return {
                "pick": f"Ambos equipos anotan en {equipo_local} vs {equipo_visitante}",
                "valor": True,
                "motivo": f"BTTS alto en ambos: local {btts_local:.2f}, visitante {btts_visitante:.2f}",
                "cuota": cuotas["btts"]
            }

        if stats_local.get("invicto_local", False) and cuotas.get("1X", 0) >= 1.55:
            return {
                "pick": f"Local o Empate (1X) en {equipo_local} vs {equipo_visitante}",
                "valor": True,
                "motivo": "Equipo local viene invicto en casa",
                "cuota": cuotas["1X"]
            }

        return {
            "pick": None,
            "valor": False,
            "motivo": "No se detectó valor real en este partido"
        }

    except Exception as e:
        return {
            "pick": None,
            "valor": False,
            "motivo": f"Error en análisis: {str(e)}"
        }
