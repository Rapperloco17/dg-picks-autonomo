from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def autenticar_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

def descargar_archivos_drive(nombre_carpeta):
    drive = autenticar_drive()
    carpeta = drive.ListFile({'q': f"title='{nombre_carpeta}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()[0]
    folder_id = carpeta['id']
    archivos = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    nombres = []
    for archivo in archivos:
        archivo.GetContentFile(archivo['title'])
        nombres.append(archivo['title'])
    return nombres

def subir_archivo_drive(nombre_carpeta, archivo_local):
    drive = autenticar_drive()
    carpeta = drive.ListFile({'q': f"title='{nombre_carpeta}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()[0]
    folder_id = carpeta['id']
    archivo_drive = drive.CreateFile({'title': os.path.basename(archivo_local), 'parents': [{'id': folder_id}]})
    archivo_drive.SetContentFile(archivo_local)
    archivo_drive.Upload()
