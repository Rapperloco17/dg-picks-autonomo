
import requests
import os
import time
from entrenar_modelo_ml import entrenar_modelos_y_enviar

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DATASET_FILENAME = "dataset_ml_base.json"
DESTINO = "input/dataset_ml_base.json"

def obtener_ultimo_json_del_bot():
    url = f"{BOT_API_URL}/getUpdates"
    response = requests.get(url).json()

    for result in reversed(response.get("result", [])):
        message = result.get("message", {})
        doc = message.get("document")
        if doc and doc["file_name"] == DATASET_FILENAME:
            return doc["file_id"]
    return None

def descargar_y_guardar(file_id, destino):
    info_url = f"{BOT_API_URL}/getFile?file_id={file_id}"
    info_res = requests.get(info_url).json()
    file_path = info_res["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    r = requests.get(file_url, stream=True)
    with open(destino, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def esperar_archivo(path, intentos=10):
    for i in range(intentos):
        if os.path.exists(path):
            print(f"✅ Archivo disponible: {path}")
            return True
        print(f"⏳ Esperando archivo {path}... ({i+1}/{intentos})")
        time.sleep(1)
    return False

def main():
    print("📥 Buscando archivo JSON en Telegram...")
    file_id = obtener_ultimo_json_del_bot()
    if not file_id:
        print("❌ No se encontró archivo válido en Telegram.")
        return

    print("⬇️ Descargando archivo a input/...")
    descargar_y_guardar(file_id, DESTINO)

    if esperar_archivo(DESTINO):
        print("🚀 Entrenando modelos con archivo actualizado...")
        entrenar_modelos_y_enviar()
        print("✅ Proceso finalizado con éxito.")
    else:
        print("❌ El archivo no se descargó correctamente.")

if __name__ == "__main__":
    main()
