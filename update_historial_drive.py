import os
import json
import requests
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_NAME = 'historial_fusionado'
API_KEY = os.environ.get("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_ASIGNADAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

# Fechas de los últimos 14 días en formato UTC
end_date = datetime.now(timezone.utc).date()
start_date = end_date - timedelta(days=14)

# Autenticación con Google Drive
def get_drive_service():
    creds_info = json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def get_folder_id(service, folder_name):
    results = service.files().list(q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                                   spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])
    return folders[0]['id'] if folders else None

def get_file_id(service, folder_id, filename):
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def download_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)

def fetch_fixtures(league_id):
    url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&from={start_date}&to={end_date}"
    print(f"Consultando: {url}")
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json().get("response", [])

def merge_fixtures(existing, nuevos):
    existentes_ids = {match['fixture']['date'] + match['teams']['home']['name'] + match['teams']['away']['name']: match for match in existing}
    for partido in nuevos:
        key = partido['fixture']['date'] + partido['teams']['home']['name'] + partido['teams']['away']['name']
        existentes_ids[key] = partido  # sobrescribe si ya existe
    return list(existentes_ids.values())

def upload_file(service, folder_id, filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(filename, mimetype='application/json')

    file_id = get_file_id(service, folder_id, filename)
    if file_id:
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"🔁 Archivo {filename} actualizado en Drive.")
    else:
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"🆕 Archivo {filename} creado en Drive.")
    os.remove(filename)

if __name__ == "__main__":
    service = get_drive_service()
    folder_id = get_folder_id(service, FOLDER_NAME)
    if not folder_id:
        print("❌ Carpeta no encontrada en Drive.")
        exit(1)

    for liga in LIGAS_ASIGNADAS:
        nombre_archivo = f"liga_{liga}.json"
        file_id = get_file_id(service, folder_id, nombre_archivo)
        existentes = []
        if file_id:
            try:
                existentes = download_file(service, file_id)
            except Exception as e:
                print(f"⚠️ No se pudo leer {nombre_archivo}: {e}")
        try:
            nuevos = fetch_fixtures(liga)
            if nuevos:
                print(f"📥 Liga {liga}: {len(nuevos)} nuevos partidos detectados")
                combinado = merge_fixtures(existentes, nuevos)
                upload_file(service, folder_id, nombre_archivo, combinado)
            else:
                print(f"➖ Liga {liga}: sin nuevos partidos en los últimos 14 días")
        except Exception as e:
            print(f"❌ Error al actualizar liga {liga}: {e}")
