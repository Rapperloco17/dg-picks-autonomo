from utils.sofascore import analizar_rompimientos_1set, analizar_ml

def obtener_picks_tenis():
    """
    Combina picks de rompimientos en primer set y ML (ganador del partido),
    generados con base en análisis real desde Sofascore.
    """
    picks = []

    resultados_romp = analizar_rompimientos_1set() if 'analizar_rompimientos_1set' in globals() else []
    resultados_ml = analizar_ml() if 'analizar_ml' in globals() else []

    for r in resultados_romp:
        if not r.get("analisis"):
            continue
        pick = {
            "partido": r["partido"],
            "pick": r["pick"],
            "cuota": r.get("cuota", "1.80"),
            "stake": "2/10",
            "canal": r["canal"],
            "analisis": r["analisis"]
        }
        picks.append(pick)

    for m in resultados_ml:
        if not m.get("analisis"):
            continue
        pick = {
            "partido": m["partido"],
            "pick": m["pick"],
            "cuota": m.get("cuota", "1.80"),
            "stake": m.get("stake", "3/10"),
            "canal": m["canal"],
            "analisis": m["analisis"]
        }
        picks.append(pick)

    return picks

