
from utils.telegram import log_envio

def enviar_mini_reto():
    print("🎯 Enviando Día 1 del Mini Reto Free...")

    mensaje = """🔥 Mini Reto Escalera – Día 1 (Versión FREE)
Pick: Gana Alcaraz
Cuota: 1.80
Stake: 2 unidades

✅ Comenzamos el mini reto gratuito. ¡Vamos con todo!"""

    log_envio("free", mensaje)

    print("✅ Mini Reto enviado al canal FREE.")
