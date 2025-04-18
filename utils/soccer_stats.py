def analizar_forma_futbol(partido):
    equipo_local = partido.get("equipo_local", "")
    equipo_visitante = partido.get("equipo_visitante", "")
    cuota = partido.get("cuota", 1.0)
    goles_local = partido.get("goles_local", [])
    goles_visita = partido.get("goles_visita", [])
    corners_local = partido.get("corners_local", [])
    corners_visita = partido.get("corners_visita", [])
    tarjetas_local = partido.get("tarjetas_local", [])
    tarjetas_visita = partido.get("tarjetas_visita", [])
    btts_local = partido.get("btts_local", [])  # lista de 1 si anotaron ambos, 0 si no
    btts_visita = partido.get("btts_visita", [])

    total_goles_local = sum(goles_local) / len(goles_local) if goles_local else 0
    total_goles_visita = sum(goles_visita) / len(goles_visita) if goles_visita else 0
    total_goles = total_goles_local + total_goles_visita

    promedio_corners = (sum(corners_local) + sum(corners_visita)) / (len(corners_local) + len(corners_visita) or 1)
    promedio_tarjetas = (sum(tarjetas_local) + sum(tarjetas_visita)) / (len(tarjetas_local) + len(tarjetas_visita) or 1)

    partidos_btts = btts_local + btts_visita
    porcentaje_btts = sum(partidos_btts) / len(partidos_btts) if partidos_btts else 0

    valor = False
    descripcion = "⚠️ Análisis equilibrado."

    if total_goles > 2.8:
        valor = True
        descripcion = f"🔥 Promedio de goles alto ({total_goles:.2f}). Puede ser buena opción OVER."
    elif total_goles < 1.8:
        valor = True
        descripcion = f"🧱 Promedio de goles bajo ({total_goles:.2f}). Se puede explorar UNDER."
    elif promedio_corners > 10:
        valor = True
        descripcion = f"🚩 Partido con promedio alto de corners ({promedio_corners:.1f}). Opción válida."
    elif promedio_tarjetas > 4:
        valor = True
        descripcion = f"🟥 Juego con promedio elevado de tarjetas ({promedio_tarjetas:.1f}). Ideal para props."
    elif porcentaje_btts > 0.7:
        valor = True
        descripcion = f"✅ Más del 70% de los partidos recientes terminaron con BTTS. Buena opción ambos anotan."

    return {
        "valor": valor,
        "descripcion": descripcion,
        "cuota": cuota,
        "prom_goles": round(total_goles, 2),
        "prom_corners": round(promedio_corners, 1),
        "prom_tarjetas": round(promedio_tarjetas, 1),
        "porcentaje_btts": round(porcentaje_btts * 100, 1)
    }


if __name__ == "__main__":
    ejemplo = {
        "equipo_local": "Arsenal",
        "equipo_visitante": "Chelsea",
        "cuota": 1.90,
        "goles_local": [2, 1, 2],
        "goles_visita": [1, 0, 2],
        "corners_local": [5, 7, 6],
        "corners_visita": [4, 5, 6],
        "tarjetas_local": [1, 2, 1],
        "tarjetas_visita": [2, 3, 1],
        "btts_local": [1, 1, 0],
        "btts_visita": [1, 1, 1]
    }
    resultado = analizar_forma_futbol(ejemplo)
    print(resultado)
