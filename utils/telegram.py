from telegram import Bot
import os

# ✅ TOKEN de tu bot (ya lo tienes configurado en Railway)
TOKEN = os.getenv("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")  # reemplaza si no usas variables de entorno

# ✅ ID de tus canales oficiales (puedes ponerlos directamente aquí o desde otras funciones)
CANAL_VIP = -1001285733813
CANAL_RETO = -1002453760512
CANAL_FREE = "@dgpickspro17"
USER_ID_DAVID = 7450739156  # Tu user_id personal para los rompimientos

bot = Bot(token=TOKEN)

# ✅ Enviar mensaje a cualquier canal
def log_envio(canal, mensaje):
    try:
        if canal == "vip":
            chat_id = CANAL_VIP
        elif canal == "reto":
            chat_id = CANAL_RETO
        elif canal == "free":
            chat_id = CANAL_FREE
        else:
            print(f"❌ Canal desconocido: {canal}")
            return

        bot.send_message(chat_id=chat_id, text=mensaje)
        print(f"✅ Mensaje enviado al canal '{canal}' correctamente.")
    except Exception as e:
        print(f"❌ Error al enviar mensaje al canal '{canal}': {e}")

# ✅ Enviar mensaje privado directo a ti
def enviar_mensaje_privado(user_id, mensaje):
    try:
        bot.send_message(chat_id=user_id, text=mensaje)
        print(f"✅ Mensaje privado enviado a {user_id}")
    except Exception as e:
        print(f"❌ Error al enviar mensaje privado a {user_id}': {e}")
