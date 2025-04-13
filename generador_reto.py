
from utils.telegram import log_envio

def enviar_reto_escalera():
    print("🚀 Enviando pick del Reto Escalera...")

    mensaje = """🔥 Reto Escalera – Día 1
Pick: Gana Djokovic
Cuota: 1.85
Stake: 5 unidades

✅ Valor detectado en la cuota."""

    log_envio("reto", mensaje)

    print("✅ Pick del Reto Escalera enviado al canal correspondiente.")
