
import requests
import time

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
    mensaje = "🚀 *DG Picks Autónomo activado con éxito!*\n\nMensaje de prueba desde Railway."
    result = send_message(mensaje)
    print(result)

    # Mantener el proceso activo
    while True:
        time.sleep(60)
