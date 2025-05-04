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
        empates_local = forma_local.count("D")
        empates_visit = forma_visit.count("D")

        pick = None
        motivo = ""
        cuota = 0

        # 🎯 OVER Markets
        if total_goles >= 3.2 and cuotas.get("over_3.5", 0) >= 2.00:
            pick = f"Más de 3.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Goles proyectados muy altos: {total_goles:.2f}"
            cuota = cuotas["over_3.5"]

        elif total_goles >= 2.6 and cuotas.get("over_2.5", 0) >= 1.75:
            pick = f"Más de 2.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Promedio de goles: {total_goles:.2f} entre ambos"
            cuota = cuotas["over_2.5"]

        elif total_goles >= 1.9 and cuotas.get("over_1.5", 0) >= 1.45:
            pick = f"Más de 1.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Probabilidad alta de al menos 2 goles"
            cuota = cuotas["over_1.5"]

        # 🎯 UNDER Markets
        elif total_goles <= 1.6 and cuotas.get("under_1.5", 0) >= 2.20:
            pick = f"Menos de 1.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Bajo promedio de goles: {total_goles:.2f}"
            cuota = cuotas["under_1.5"]

        elif total_goles <= 2.0 and cuotas.get("under_2.5", 0) >= 1.90:
            pick = f"Menos de 2.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Partido con tendencia a pocos goles"
            cuota = cuotas["under_2.5"]

        elif total_goles <= 3.0 and cuotas.get("under_3.5", 0) >= 1.55:
            pick = f"Menos de 3.5 goles en {equipo_local} vs {equipo_visitante}"
            motivo = f"Previsión moderada de goles"
            cuota = cuotas["under_3.5"]

        # 🎯 Ambos Anotan
        elif btts_local >= 0.6 and btts_visit >= 0.6 and cuotas.get("btts", 0) >= 1.80:
            pick = f"Ambos equipos anotan en {equipo_local} vs {equipo_visitante}"
            motivo = f"BTTS alto en ambos: local ({btts_local:.2f}), visitante ({btts_visit:.2f})"
            cuota = cuotas["btts"]

        # 🎯 Doble oportunidad
        elif stats_local.get("invicto_local", False) and cuotas.get("1X", 0) >= 1.55:
            pick = f"Local o Empate (1X) en {equipo_local} vs {equipo_visitante}"
            motivo = "El local está invicto en casa"
            cuota = cuotas["1X"]

        elif stats_visit.get("invicto_visitante", False) and cuotas.get("X2", 0) >= 1.60:
            pick = f"Empate o Visitante (X2) en {equipo_local} vs {equipo_visitante}"
            motivo = "El visitante se mantiene invicto fuera"
            cuota = cuotas["X2"]

        elif victorias_local >= 2 and derrotas_visit >= 2 and cuotas.get("12", 0) >= 1.45:
            pick = f"1 o 2 (sin empate) en {equipo_local} vs {equipo_visitante}"
            motivo = "Equipos con tendencia decidida (sin empates recientes)"
            cuota = cuotas["12"]

        # 🎯 ML directo
        elif victorias_local >= 3 and cuotas.get("ml_local", 0) >= 1.75:
            pick = f"{equipo_local} gana vs {equipo_visitante}"
            motivo = f"{equipo_local} viene fuerte con 3+ victorias"
            cuota = cuotas["ml_local"]

        elif derrotas_visit >= 3 and cuotas.get("ml_visitante", 0) >= 1.90:
            pick = f"{equipo_visitante} gana vs {equipo_local}"
            motivo = f"{equipo_local} viene en mala racha"
            cuota = cuotas["ml_visitante"]

        elif empates_local >= 3 and empates_visit >= 2 and cuotas.get("empate", 0) >= 3.20:
            pick = f"Empate entre {equipo_local} y {equipo_visitante}"
            motivo = "Ambos con tendencia reciente a empatar"
            cuota = cuotas["empate"]

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


