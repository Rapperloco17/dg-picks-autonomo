import requests

def send_message_telegram(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Error al enviar mensaje: {response.status_code} - {response.text}")
        else:
            print("📤 Mensaje enviado correctamente a Telegram.")
    except Exception as e:
        print(f"Error de conexión al enviar mensaje: {e}")

def log_envio(contexto, mensaje):
    print(f"📤 Enviando mensaje desde {contexto}:\n{mensaje}\n")

# ✅ TOKEN y CHAT IDs OFICIALES DE DG PICKS
BOT_TOKEN = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"

CHAT_IDS = {
    "vip": "-1001285733813",         # Canal VIP (privado)
    "reto": "-1002453760512",        # Canal Reto Escalera
    "free": "@dgpickspro17",         # Canal Free (público)
    "admin": "7450739156"            # Admin personal
}
