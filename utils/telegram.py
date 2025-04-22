# utils/telegram.py – Envío automático a Telegram para DG Picks
import requests

# TOKEN del bot y chat IDs oficiales
BOT_TOKEN = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"

# Canales oficiales
CHAT_IDS = {
    "VIP": -1001285733813,
    "RETO": -1002453760512,
    "FREE": "@dgpickspro17",
    "ADMIN": "7450739156"  # usuario administrador
}

def enviar_mensaje(mensaje, canal="VIP"):
    """
    Envía un mensaje a un canal de Telegram según la clave especificada: VIP, FREE, RETO, ADMIN
    """
    try:
        chat_id = CHAT_IDS.get(canal)
        if not chat_id:
            raise ValueError(f"Canal '{canal}' no está configurado.")

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        }

        response = requests.post(url, data=data)
        if not response.ok:
            print(f"⚠️ Error al enviar mensaje a {canal}: {response.text}")
        else:
            print(f"✅ Enviado con éxito a canal {canal}")

    except Exception as e:
        print(f"⚠️ Error general al enviar mensaje a Telegram ({canal}):", e)
