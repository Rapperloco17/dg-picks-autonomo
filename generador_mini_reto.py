
from utils.telegram import log_envío

def enviar_mini_reto():
    print("🎯 Enviando Día 1 del Mini Reto Free...")

    mensaje = """🔥 Mini Reto Escalera – Día 1 (Versión FREE)
Pick: Gana Alcaraz
Cuota: 1.80
Stake: 2 unidades

✅ Comenzamos el mini reto gratuito. ¡Vamos con todo!"""

    log_envío("free", mensaje)

    print("✅ Mini Reto enviado al canal FREE.")
