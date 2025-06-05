import requests
import dicttoxml

BOT_TOKEN = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"
CHAT_ID = "7450739156"

archivos = ["39.json", "40.json"]
BASE_URL = "https://raw.githubusercontent.com/Rapperloco17/dg-picks-autonomo/main/historial/"

def enviar_a_telegram(nombre_archivo):
    with open(nombre_archivo, "rb") as f:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            data={"chat_id": CHAT_ID},
            files={"document": (nombre_archivo, f)}
        )
        if response.status_code == 200:
            print(f"📤 Enviado a Telegram: {nombre_archivo}")
        else:
            print(f"❌ Error al enviar {nombre_archivo}: {response.text}")

for archivo in archivos:
    url = BASE_URL + archivo
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        xml_data = dicttoxml.dicttoxml(data, custom_root='data', attr_type=False)

        nombre_xml = archivo.replace(".json", ".xml")
        with open(nombre_xml, "wb") as f:
            f.write(xml_data)

        print(f"✅ Guardado: {nombre_xml}")
        enviar_a_telegram(nombre_xml)

    else:
        print(f"❌ Error al leer {archivo}: {response.status_code}")
