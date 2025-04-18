def analizar_forma_futbol(equipo, stats_equipo):
    partidos = stats_equipo.get("last_5", [])
    goles_hechos = 0
    goles_recibidos = 0
    victorias = 0

    for p in partidos:
        if p["team"]["name"].lower() == equipo.lower():
            goles_hechos += p["goals"]["for"]
            goles_recibidos += p["goals"]["against"]
            if p["goals"]["for"] > p["goals"]["against"]:
                victorias += 1
        else:
            goles_hechos += p["goals"]["against"]
            goles_recibidos += p["goals"]["for"]
            if p["goals"]["against"] > p["goals"]["for"]:
                victorias += 1

    forma = {
        "promedio_goles_hechos": goles_hechos / len(partidos) if partidos else 0,
        "promedio_goles_recibidos": goles_recibidos / len(partidos) if partidos else 0,
        "victorias": victorias,
        "total": len(partidos),
    }

    return forma
