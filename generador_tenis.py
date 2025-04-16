from utils.sofascore import obtener_picks_tenis
from utils.telegram import log_envio, enviar_mensaje_privado

def enviar_picks_tenis():
    picks = obtener_picks_tenis()
    total_picks = len(picks)

    # 📢 Resumen para control
    resumen = f"📋 DG Picks Tenis ejecutado.\n"
    resumen += f"📆 Picks generados: {total_picks}\n"

    if total_picks == 0:
        resumen += "❌ No se encontraron picks de valor para hoy.\n"
    else:
        resumen += "✅ Se enviarán los picks generados.\n"

    enviar_mensaje_privado(resumen)

    for pick in picks:
        if "canal" not in pick:
            print("❌ Pick sin canal definido:", pick)
            continue

        mensaje = (
            f"🏁 {pick['pick']}\n"
            f"📅 Partido: {pick['partido']}\n"
            f"🔢 Análisis: {pick['analisis']}\n"
            f"💲 Cuota: {pick['cuota']}\n"
            f"⚖️ Stake: {pick['stake']}\n"
            f"✅ Valor detectado en la cuota."
        )

        if pick['canal'] == "privado":
            enviar_mensaje_privado(mensaje)
        else:
            log_envio(pick['canal'], mensaje)
