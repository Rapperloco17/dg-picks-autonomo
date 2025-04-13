# Archivo: generador_mini_reto.py

from utils.telegram import log_envio

def enviar_mini_reto_escalera():
    mensaje = """
🔥 MINI RETO ESCALERA – Día 1 🔥

🧠 Pick: Ejemplo de apuesta segura
💵 Cuota: 1.85
📊 Stake: 1/10

🎯 Objetivo: convertir 1 unidad en 10 en pocos días.
⚠️ Apuesta responsable.

¿Te unes al reto? 🚀
    """
    log_envio('free', mensaje)
