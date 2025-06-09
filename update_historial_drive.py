import requests
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import asyncio
import platform

# Configuración de la API de Football
API_KEY = os.getenv("API_FOOTBALL_KEY", "17b86e41b9d4d3b5f096efe377")
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}
MAX_PARTIDOS = int(os.getenv("MAX_PARTIDOS", "20"))

# Prueba con league_id y season fijos
league_id = 39  # Premier League
season = 2024   # Temporada reciente
url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}"

# Configuración de Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=credentials)

async def main():
    # Obtener fixtures de la API
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Lanza error si el estado no es 200
    fixtures = response.json().get("response", [])

    # Limitar a MAX_PARTIDOS
    fixtures = fixtures[:MAX_PARTIDOS]

    # Guardar en Google Drive
    file_name = f"liga_{league_id}.json"
    file_metadata = {"name": file_name, "parents": ["historial_fusionado"]}
    file_content = json.dumps(fixtures, ensure_ascii=False).encode("utf-8")
    try:
        # Buscar si el archivo existe
        query = f"name='{file_name}' and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        if files:
            file_id = files[0]["id"]
            drive_service.files().update(fileId=file_id, media_body=file_content, fields="id").execute()
        else:
            file = drive_service.files().create(body=file_metadata, media_body=file_content, fields="id").execute()
        print(f"✅ Archivo {file_name} sobreescrito en Google Drive.")
    except Exception as e:
        print(f"❌ Error al guardar en Drive: {e}")

    # Actualizar total de partidos
    total_partidos = len(fixtures)
    print(f"✅ Actualizados {total_partidos} partidos en total.")

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
