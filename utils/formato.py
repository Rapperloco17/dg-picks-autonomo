# utils/formato.py – Formato profesional para mensajes de picks en DG Picks

def formatear_pick(analisis):
    """
    Recibe el diccionario 'analisis' con datos del pick y devuelve un mensaje formateado listo para Telegram.
    """
    try:
        partido = analisis.get("partido", "Partido no especificado")
        pick = analisis.get("pick", "Sin pick")
        cuota = analisis.get("cuota", "?")
        justificacion = analisis.get("justificacion", "Sin justificación")

        mensaje = f"<b>🌟 PICK DEL DÍA</b>\n"
        mensaje += f"<b>Partido:</b> {partido}\n"
        mensaje += f"<b>Pick:</b> {pick}\n"
        mensaje += f"<b>Cuota:</b> {cuota}\n"
        mensaje += f"<b>Justificación:</b> {justificacion}\n"
        mensaje += f"\n✅ Valor detectado en la cuota"

        return mensaje

    except Exception as e:
        return f"\u26a0\ufe0f Error al formatear pick: {e}"
