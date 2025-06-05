import requests
import json

# Lista de archivos que quieres validar desde GitHub
ARCHIVOS = [
    "39.json",
    "40.json",
]

BASE_URL = "https://raw.githubusercontent.com/Rapperloco17/dg-picks-autonomo/main/historial/"

total_general = 0

for archivo in ARCHIVOS:
    url = BASE_URL + archivo
    try:
        response = requests.get(url)
        data = response.json()

        if isinstance(data, list):
            cantidad = len(data)
        elif isinstance(data, dict) and "response" in data:
            cantidad = len(data["response"])
        else:
            cantidad = 0

        total_general += cantidad
        print(f"📁 Archivo: {archivo} → {cantidad} juegos")

    except Exception as e:
        print(f"❌ Error leyendo {archivo}: {e}")

print(f"\n✅ Total general: {total_general} partidos")
