from utils.sofascore import obtener_picks_tenis
from utils.telegram import enviar_mensaje_privado, log_envio


def enviar_picks_tenis():
    picks = obtener_picks_tenis()
    total_picks = len(picks)

    # ✉️ Mensaje de resumen para administrador
    resumen = f"📋 DG Picks Tenis ejecutado.\n"
    resumen += f"📆 Picks generados: {total_picks}\n"

    if total_picks == 0:
        resumen += "❌ No se encontraron picks de valor para hoy.\n"
    else:
        resumen += "✅ Se enviarán los picks generados.\n"

    # Enviar mensaje de control al administrador
    enviar_mensaje_privado(7450739156, resumen)

    # Enviar picks si hay
    for pick in picks:
        if "canal" not in pick:
            print("❌ No se especificó el canal para este pick:", pick)
            continue

        mensaje = (
            f"🏁 Pick Tenis\n"
            f"📅 Partido: {pick['partido']}\n"
            f"🔢 Análisis: {pick['analisis']}\n"
            f"💲 Cuota: {pick['cuota']}\n"
            f"⚖️ Stake: {pick['stake']}\n"
            f"✅ Valor detectado en la cuota."
        )
        log_envio(pick["canal"], mensaje)
