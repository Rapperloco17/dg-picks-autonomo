def interpretar_resultado_pick(pick, resultado):
    if not resultado:
        return "desconocido"

    tipo = pick.get("tipo")
    goles_local = resultado.get("goles_local", 0)
    goles_visita = resultado.get("goles_visita", 0)
    total_goles = goles_local + goles_visita

    # Normalizar nombres de equipos
    equipo_pick = pick.get("equipo", "").lower()
    local = resultado.get("nombre_local", "").lower()
    visita = resultado.get("nombre_visita", "").lower()

    if tipo == "ML":
        if equipo_pick in local and goles_local > goles_visita:
            return "ganado"
        elif equipo_pick in visita and goles_visita > goles_local:
            return "ganado"
        else:
            return "perdido"

    elif tipo == "OVER":
        linea = float(pick.get("linea", 2.5))
        return "ganado" if total_goles > linea else "perdido"

    elif tipo == "UNDER":
        linea = float(pick.get("linea", 2.5))
        return "ganado" if total_goles < linea else "perdido"

    elif tipo == "BTTS":  # Ambos anotan
        return "ganado" if goles_local > 0 and goles_visita > 0 else "perdido"

    # Si es tipo desconocido o falta info
    return "desconocido"


if __name__ == "__main__":
    pick = {
        "tipo": "OVER",
        "linea": 2.5,
        "equipo": "Arsenal",
        "partido": "Arsenal vs Chelsea"
    }

    resultado = {
        "goles_local": 2,
        "goles_visita": 1,
        "nombre_local": "Arsenal",
        "nombre_visita": "Chelsea"
    }

    print(interpretar_resultado_pick(pick, resultado))
