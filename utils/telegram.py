# utils/telegram.py

import requests

# Token del bot de Telegram
TELEGRAM_BOT_TOKEN = '7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA'

# IDs de los canales de Telegram
CHANNELS = {
    'vip': '@dgpicksvippro',       # Canal VIP
    'reto': '@f2dqWWjYggJmM2Jh',    # Canal Reto Escalera
    'free': '@dgpicks17'           # Canal Free
}

def enviar_mensaje(canal: str, mensaje: str):
    """
    Envía un mensaje a un canal de Telegram según el nombre del canal.

    Parámetros:
        canal (str): Puede ser 'vip', 'reto' o 'free'.
        mensaje (str): Texto del mensaje que se enviará.

    Ejemplo de uso:
        enviar_mensaje('vip', '📢 ¡Este es un mensaje para el canal VIP!')
    """
    if canal not in CHANNELS:
        raise ValueError(f"⚠️ Canal '{canal}' no está configurado en CHANNELS.")

    chat_id = CHANNELS[canal]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'HTML'
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print(f"✅ Mensaje enviado correctamente al canal '{canal}'.")
    else:
        print(f"❌ Error al enviar el mensaje al canal '{canal}': {response.text}")
