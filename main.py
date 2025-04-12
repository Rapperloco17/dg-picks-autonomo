import requests
import schedule
import time
from datetime import datetime

# Token y canal de Telegram
TOKEN = "7520899056:AAHaSZ1d5G8a9HlYzX6NYJ6fCnZsADTOFA"
CHANNEL_USERNAME = "@dgpicksvippro"

# Función para enviar mensaje al canal
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_USERNAME,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    return response.json()

# Función programada que contiene los picks
def enviar_picks_tenis():
    mensaje = "🎾 *PICKS DE TENIS DEL DÍA*\n\n1. Taberner gana\n2. Martineau rompe 1er set\n3. Moro Cañas gana al menos 1 set\n\n✅ Valor detectado en cada pick."
    send_message(mensaje)
    print("✅ Picks enviados automáticamente a las 22:00.")

# Programación diaria a las 22:00 (hora de México)
schedule.every().day.at("22:00").do(enviar_picks_tenis)

# Bucle para que corra siempre
while True:
    schedule.run_pending()
    time.sleep(1)
