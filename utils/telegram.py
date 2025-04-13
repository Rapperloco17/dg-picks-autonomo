# IDs de los canales de Telegram
CHANNELS = {
    'vip': -1002606141968,        # Canal VIP+
    'reto': -1002453760512,      # Canal Reto Escalera
    'free': '@dgpickspro17'      # Canal Free (ahora público, se usa @username)
}

def log_envío(canal: str, mensaje: str):
    """
    Envía un mensaje a un canal de Telegram según el nombre del canal.

    Parámetros:
        canal (str): Puede ser 'vip', 'reto' o 'free'.
        mensaje (str): Texto del mensaje que se enviará.

    Ejemplo de uso:
        log_envio('vip', '¡Este es un mensaje para el canal VIP!')
    """
    if canal not in CHANNELS:
        raise ValueError(f"❌ Canal '{canal}' no está configurado en CHANNELS.")

    chat_id = CHANNELS[canal]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'HTML'
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        print(f"❌ Error al enviar el mensaje al canal '{canal}': {response.text}")
    else:
        print(f"✅ Mensaje enviado al canal '{canal}' correctamente.")
