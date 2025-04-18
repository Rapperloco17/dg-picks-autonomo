import requests

def send_message_telegram(mensaje, canal="VIP"):
    canales = {
        "VIP": "-1001285733813",
        "FREE": "@dgpickspro17",
        "RETO": "-1002453760512"
    }
    chat_id = canales.get(canal)
    if not chat_id:
        print(f"❌ Canal no reconocido: {canal}")
        return

    token = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"❌ Error al enviar mensaje: {response.text}")
    else:
        print("✅ Mensaje enviado con éxito")
