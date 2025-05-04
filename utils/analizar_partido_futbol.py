# utils/analizar_partido_futbol.py

def analizar_partido_futbol(partido, datos_estadisticos, cuotas):
    try:
        equipo_local = partido["teams"]["home"]["name"]
        equipo_visitante = partido["teams"]["away"]["name"]

        stats_local = datos_estadisticos.get("local", {})
        stats_visit = datos_estadisticos.get("visitante", {})

        total_goles = stats_local.get("goles_promedio", 0) + stats_visit.get("goles_promedio", 0)
        btts_local = stats_local.get("btts", 0)
        btts_visit = stats_visit.get("btts", 0)

        # Análisis Over 2.5
        if total_goles >= 2.8 and cuotas.get("over_2.5", 0) >= 1.75:
            return {
                "pick": f"Más de 2.5 goles en {equipo_local} vs {equipo_visitante}",
                "valor": True,
                "motivo": f"Promedio de goles alto: {total_goles:.2f} entre ambos equipos",
                "cuota": cuotas["over_2.5"]
            }

        # Análisis BTTS
        if btts_local >= 0.6 and btts_visit >= 0.6 and cuotas.get("btts", 0) >= 1.80:
            return {
                "pick": f"Ambos equipos anotan en {equipo_local} vs {equipo_visitante}",
                "valor": True,
                "motivo": f"BTTS alto en ambos: local ({btts_local:.2f}), visitante ({btts_visit:.2f})",
                "cuota": cuotas["btts"]
            }

        # Análisis 1X si el local viene invicto en casa
        if stats_local.get("invicto_local", False) and cuotas.get("1X", 0) >= 1.55:
            return {
                "pick": f"Local o Empate (1X) en {equipo_local} vs {equipo_visitante}",
                "valor": True,
                "motivo": "Equipo local viene invicto en casa",
                "cuota": cuotas["1X"]
            }

        # Si no hay valor real
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

