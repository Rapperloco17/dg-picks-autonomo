import requests
import os
import json
from entrenar_modelo_ml import entrenar_modelos_y_enviar

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
CHAT_ID_ADMIN = "7450739156"  # tu ID

def obtener_ultimo_json_del_bot():
    url = f"{BOT_API_URL}/getUpdates"
    response = requests.get(url)
    updates = response.json()

    for result in reversed(updates.get("result", [])):
        message = result.get("message", {})
        doc = message.get("document")
        if doc and doc["file_name"].endswith(".json"):
            return doc["file_id"]
    return None

def descargar_archivo(file_id, destino):
    file_info_url = f"{BOT_API_URL}/getFile?file_id={file_id}"
    file_info = requests.get(file_info_url).json()
    file_path = file_info["result"]["file_path"]

    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    r = requests.get(file_url)
    with open(destino, "wb") as f:
        f.write(r.content)

def main():
    print("🧠 Buscando dataset previo en Telegram...")
    file_id = obtener_ultimo_json_del_bot()

    if not file_id:
        print("❌ No se encontró un archivo JSON en los mensajes recientes.")
        return

    print("⬇️ Descargando archivo...")
    descargar_archivo(file_id, "dataset_ml_base.json")
    print("✅ Dataset descargado como dataset_ml_base.json")

    entrenar_modelos_y_enviar()

if __name__ == "__main__":
    main()
