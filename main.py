
import requests
import time
from datetime import datetime

TOKEN = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"
CHANNEL_USERNAME = "@dgpicksvippro"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_USERNAME,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    return response.json()

if __name__ == "__main__":
    # Simulamos un mensaje con fecha (en producción, esto viene de tu generador de picks)
    mensaje = "🧩 PARLAY MLB DEL DÍA – 10/04/2025\n1. NY Yankees\n2. SD Padres\n3. BAL Orioles\n💰 Cuota: 6.39\n🔥 Stake: 2/10"

    hoy = datetime.now().strftime("%d/%m/%Y")

    if hoy in mensaje:
        send_message(mensaje)
        print("✅ Pick enviado.")
    else:
        print("⏳ Pick no enviado: no es del día.")

    while True:
        time.sleep(60)
