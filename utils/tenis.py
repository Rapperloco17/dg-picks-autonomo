from utils.sofascore import analizar_rompimientos_1set

def obtener_picks_tenis():
    """
    Obtiene picks diarios reales con enfoque en rompimientos y no rompimientos
    en el primer set, utilizando análisis de Sofascore.
    """
    picks = []

    resultados = analizar_rompimientos_1set()

    for r in resultados:
        # Si no hay análisis, lo ignoramos
        if not r.get("analisis"):
            continue

        pick = {
            "partido": r["partido"],
            "pick": r["pick"],
            "cuota": r.get("cuota", "1.80"),  # Puedes ajustar esto manualmente después
            "stake": "2/10",
            "canal": r["canal"],
            "analisis": r["analisis"]
        }

        picks.append(pick)

    return picks


