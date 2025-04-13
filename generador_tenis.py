from utils.tenis import obtener_picks_tenis
from utils.telegram import log_envio

def enviar_picks_tenis():
    picks = obtener_picks_tenis()

    for pick in picks:
        mensaje = (
            f"🎾 Pick Tenis\n"
            f"📌 Pick: {pick['pick']}\n"
            f"📊 Cuota: {pick['cuota']}\n"
            f"🔥 Stake: {pick['stake']}\n"
            f"📋 Análisis: {pick['analisis']}\n"
            f"✅ Valor detectado en la cuota."
        )
       log_envio(pick["canal"], mensaje)
