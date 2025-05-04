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

        forma_local = stats_local.get("forma", [])
        forma_visit = stats_visit.get("forma", [])
        victorias_local = forma_local.count("W")
        derrotas_visit = forma_visit.count("L")

        pick = None
        motivo = ""
        cuota = 0

        # 🟢 Over 2.5
        if total_goles >= 2.8 and cuotas.get("over_2.5", 0) >= 1.75:
            pick = f"Más de 2.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Promedio de goles alto: {total_goles:.2f} entre ambos"
            cuota = cuotas["over_2.5"]

        # 🟢 Ambos Anotan
        elif btts_local >= 0.6 and btts_visit >= 0.6 and cuotas.get("btts", 0) >= 1.80:
            pick = f"Ambos equipos anotan en {equipo_local} vs {equipo_visitante}"
            motivo = f"BTTS alto: local ({btts_local:.2f}), visitante ({btts_visit:.2f})"
            cuota = cuotas["btts"]

        # 🟢 Local o Empate
        elif stats_local.get("invicto_local", False) and cuotas.get("1X", 0) >= 1.55:
            pick = f"Local o Empate (1X) en {equipo_local} vs {equipo_visitante}"
            motivo = "Equipo local invicto en casa"
            cuota = cuotas["1X"]

        # 🟢 Empate NO válido si el visitante viene mal
        elif derrotas_visit >= 3 and cuotas.get("draw_no_bet_home", 0) >= 1.65:
            pick = f"Empate NO válido (local) en {equipo_local} vs {equipo_visitante}"
            motivo = f"Visitante con 3 o más derrotas recientes"
            cuota = cuotas["draw_no_bet_home"]

        # 🟡 Local gana directo si viene muy fuerte
        elif victorias_local >= 3 and cuotas.get("ml_local", 0) >= 1.80:
            pick = f"{equipo_local} gana vs {equipo_visitante}"
            motivo = f"{equipo_local} viene con 3+ victorias recientes"
            cuota = cuotas["ml_local"]

        if pick:
            return {
                "pick": pick,
                "valor": True,
                "motivo": motivo,
                "cuota": cuota
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

