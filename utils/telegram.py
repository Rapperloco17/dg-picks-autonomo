import requests
import os

# Reemplaza esto con tu verdadero token y chat_id si no usas variables de entorno
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "AQUI_TU_TOKEN"
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or "@nombre_de_tu_canal_o_id"

def log_envío(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"❌ Error al enviar mensaje a Telegram: {response.text}")
        else:
            print("📩 Mensaje enviado a Telegram con éxito.")
    except Exception as e:
        print(f"⚠️ Excepción al enviar mensaje: {e}")
