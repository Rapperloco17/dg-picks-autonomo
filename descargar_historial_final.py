
import requests
import json
import os
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Autenticación con Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# ID de la carpeta en Google Drive que contiene el historial
FOLDER_ID = '1TqOh0ODcrnUdtz2omT8tCXrLobmMdwAz'

# Descargar todos los archivos JSON de la carpeta
file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()

if not os.path.exists("descargas_drive"):
    os.makedirs("descargas_drive")

print(f"📥 Descargando {len(file_list)} archivos...")

for file in file_list:
    if file['title'].endswith('.json'):
        file_path = os.path.join("descargas_drive", file['title'])
        file.GetContentFile(file_path)
        print(f"✅ {file['title']} descargado.")

print("🎯 Listo. Ya puedes procesar los archivos localmente.")
