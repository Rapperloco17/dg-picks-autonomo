from utils.telegram import log_envío

# Mensaje del pick manual
mensaje = "💣 PICK MANUAL DG PICKS 💣\n\n🧠 Volkanovski gana por KO/TKO a López (UFC)\n🔥 Stake: 2/10\n\n📢 ¡Solo para valientes, esto se va a cobrar!"

# Enviar a los 3 canales
try:
    log_envío('vip', mensaje)
    print("✅ Enviado al canal VIP")
except Exception as e:
    print(f"❌ Error al enviar al canal VIP: {e}")

try:
    log_envío('reto', mensaje)
    print("✅ Enviado al canal RETO ESCALERA")
except Exception as e:
    print(f"❌ Error al enviar al canal RETO: {e}")

try:
    log_envío('free', mensaje)
    print("✅ Enviado al canal FREE")
except Exception as e:
    print(f"❌ Error al enviar al canal FREE: {e}")
