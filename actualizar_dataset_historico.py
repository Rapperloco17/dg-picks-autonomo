import requests
import os
import time
from entrenar_modelo_ml import entrenar_modelos_y_enviar

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DATASET_FILENAME = "dataset_ml_base.json"

def obtener_ultimo_json_del_bot():
    url = f"{BOT_API_URL}/getUpdates"
    response = requests.get(url).json()

    for result in reversed(response.get("result", [])):
        message = result.get("message", {})
        doc = message.get("document")
        if doc and doc["file_name"] == DATASET_FILENAME:
            return doc["file_id"]
    return None

def descargar_archivo(file_id):
    file_info_url = f"{BOT_API_URL}/getFile?file_id={file_id}"
    file_info = requests.get(file_info_url).json()
    file_path = file_info["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

    response = requests.get(file_url)
    with open(DATASET_FILENAME, "wb") as f:
        f.write(response.content)

def esperar_archivo():
    for i in range(10):
        if os.path.exists(DATASET_FILENAME):
            print(f"✅ Archivo {DATASET_FILENAME} encontrado.")
            return True
        print(f"⏳ Esperando archivo... ({i+1}/10)")
        time.sleep(1)
    return False

def main():
    print("📥 Buscando archivo JSON en Telegram...")
    file_id = obtener_ultimo_json_del_bot()
    if not file_id:
        print("❌ No se encontró archivo válido en Telegram.")
        return

    print("⬇️ Descargando archivo JSON...")
    descargar_archivo(file_id)

    print("🧠 Validando existencia del archivo...")
    if esperar_archivo():
        print("🚀 Entrenando modelos...")
        entrenar_modelos_y_enviar()
        print("✅ Proceso completo.")
    else:
        print("❌ El archivo no se descargó correctamente.")

if __name__ == "__main__":
    main()
