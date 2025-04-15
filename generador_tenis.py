from utils.tenis import obtener_picks_tenis
from utils.telegram import log_envio, enviar_mensaje_privado

def enviar_picks_tenis():
    picks = obtener_picks_tenis()

    for pick in picks:
        if "canal" not in pick:
            print("❌ No se especificó el canal para este pick:", pick)
            continue

        mensaje = (
            f"🎾 Pick Tenis\n"
            f"📌 {pick['partido']}\n"
            f"🧠 Análisis: {pick['analisis']}\n"
            f"💸 Cuota: {pick['cuota']}\n"
            f"📊 Stake: {pick['stake']}\n"
            f"✅ Valor detectado en la cuota."
        )

        # Si el pick es de rompimiento, mandarlo directo al admin
        if any(kw in pick['pick'].lower() for kw in ["rompe", "no rompe", "ambos rompen", "solo uno rompe"]):
            enviar_mensaje_privado(7450739156, mensaje)
        else:
            log_envio(pick["canal"], mensaje)

