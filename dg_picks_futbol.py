def calcular_stats(equipo, partidos):
    goles_favor = []
    goles_contra = []
    btts = []
    over25 = []

    for p in partidos:
        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")
        goles_local = p.get("goles_local")
        goles_visitante = p.get("goles_visitante")

        # Saltar si falta algún dato
        if local is None or visitante is None or goles_local is None or goles_visitante is None:
            continue

        if equipo == local or equipo == visitante:
            if equipo == local:
                gf = goles_local
                gc = goles_visitante
            else:
                gf = goles_visitante
                gc = goles_local

            goles_favor.append(gf)
            goles_contra.append(gc)
            btts.append(1 if goles_local > 0 and goles_visitante > 0 else 0)
            over25.append(1 if goles_local + goles_visitante > 2.5 else 0)

    total = len(goles_favor)
    if total == 0:
        return {"juegos": 0, "goles_favor": 0, "goles_contra": 0, "btts_pct": 0, "over25_pct": 0}

    return {
        "juegos": total,
        "goles_favor": sum(goles_favor) / total,
        "goles_contra": sum(goles_contra) / total,
        "btts_pct": 100 * sum(btts) / total,
        "over25_pct": 100 * sum(over25) / total
    }
