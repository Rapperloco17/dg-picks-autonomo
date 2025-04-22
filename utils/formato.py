# utils/formato.py (con log_seguro aplicado)

def log_seguro(texto):
    try:
        print(texto.encode("utf-8", "ignore").decode("utf-8"))
    except:
        pass

def formatear_pick(analisis):
    partido = analisis["partido"]
    tipo = analisis["tipo"]
    pick = analisis["pick"]
    cuota = analisis["cuota"]
    justificacion = analisis["justificacion"]

    mensaje = (
        f"\n✨ PICK DEL DÍA\n"
        f"Partido: {partido}\n"
        f"Pick: {pick}\n"
        f"Cuota: {cuota}\n"
        f"Justificación: {justificacion}\n"
        f"✅ Valor detectado en la cuota"
    )

    log_seguro(f"✅ Pick generado para {partido}")
    return mensaje
