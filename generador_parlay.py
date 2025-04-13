
from utils.telegram import log_envio

def enviar_parlay_diario():
    print("💥 Generando Parlay Diario...")

    mensaje_vip = """💎 Parlay VIP del Día
1. Djokovic gana un set
2. Dodgers ML
3. Over 2.5 goles en Real Madrid vs Barcelona

💰 Cuota total: 4.25
✅ Valor detectado en la cuota."""

    mensaje_free = """🔥 Parlay FREE del Día
1. Djokovic gana un set
2. Dodgers ML

💰 Cuota: 2.50
🎁 ¿Quieres el parlay completo? Únete al canal VIP."""

    log_envio("vip", mensaje_vip)
    log_envio("free", mensaje_free)

    print("✅ Parlay enviado a VIP y FREE.")
