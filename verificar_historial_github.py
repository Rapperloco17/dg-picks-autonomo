import requests
import dicttoxml

# Lista de archivos a procesar
archivos = ["39.json", "40.json"]
BASE_URL = "https://raw.githubusercontent.com/Rapperloco17/dg-picks-autonomo/main/historial/"

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
    else:
        print(f"❌ Error al leer {archivo}: {response.status_code}")
