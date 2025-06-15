import requests
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime

# Configuración
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDS_CONTENT = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')  # Obtener el JSON de la variable de entorno
if CREDS_CONTENT:
    # Guardar temporalmente el JSON si es una cadena
    with open('temp_credentials.json', 'w') as f:
        f.write(CREDS_CONTENT)
    CREDS_FILE = 'temp_credentials.json'
else:
    CREDS_FILE = 'credentials.json'  # Fallback local (para pruebas)
FOLDER_NAME = 'historial_fusionado'
API_KEY = os.environ.get("API_KEY")  # Leer desde Railway
HEADERS = {"x-apisports-key": API_KEY}
LIGAS_ASIGNADAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

# Autenticación de Google Drive
def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"❌ Error en autenticación de Google Drive: {e}")
            raise
    return build('drive', 'v3', credentials=creds)

# Obtener o crear carpeta en Google Drive
def get_or_create_folder(service, folder_name):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    if folders:
        return folders[0]['id']
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

# Obtener datos de la API de Football con estadísticas detalladas
def fetch_football_data():
    historial = {}
    seasons = [2024, 2025]
    for season in seasons:
        for league_id in LIGAS_ASIGNADAS:
            historial[league_id] = []
            url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}"
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                fixtures = response.json().get('response', [])
                print(f"✅ Recibidos {len(fixtures)} fixtures para liga {league_id}, temporada {season}")
                for fixture in fixtures:
                    fixture_id = fixture['fixture']['id']
                    match = {
                        "teams": {
                            "home": {"name": fixture['teams']['home']['name']},
                            "away": {"name": fixture['teams']['away']['name']}
                        },
                        "goals": {
                            "home": fixture['goals']['home'] if fixture['goals']['home'] is not None else 0,
                            "away": fixture['goals']['away'] if fixture['goals']['away'] is not None else 0
                        },
                        "league": {"id": league_id, "name": fixture['league']['name']},
                        "fixture": {"date": fixture['fixture']['date']}
                    }
                    # Obtener estadísticas detalladas
                    try:
                        r_stats = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}", headers=HEADERS)
                        r_stats.raise_for_status()
                        stats_data = r_stats.json().get("response", [])
                        if stats_data:
                            stats = {}
                            for team_stats in stats_data:
                                team_name = team_stats["team"]["name"]
                                if team_name == match["teams"]["home"]["name"]:
                                    stats["home"] = team_stats["statistics"]
                                elif team_name == match["teams"]["away"]["name"]:
                                    stats["away"] = team_stats["statistics"]
                            if stats:
                                match["stats"] = {
                                    "goles_1t": {
                                        "home": stats["home"].get("goals", {}).get("first_half", "N/A"),
                                        "away": stats["away"].get("goals", {}).get("first_half", "N/A")
                                    },
                                    "corners": {
                                        "home": stats["home"].get("corners", {}).get("total", "N/A"),
                                        "away": stats["away"].get("corners", {}).get("total", "N/A")
                                    },
                                    "shots": {
                                        "home": stats["home"].get("shots", {}).get("total", "N/A"),
                                        "away": stats["away"].get("shots", {}).get("total", "N/A")
                                    },
                                    "cards": {
                                        "home": stats["home"].get("cards", {}).get("total", "N/A"),
                                        "away": stats["away"].get("cards", {}).get("total", "N/A")
                                    },
                                    "shots_on_goal": {
                                        "home": stats["home"].get("shots_on_goal", {}).get("total", "N/A"),
                                        "away": stats["away"].get("shots_on_goal", {}).get("total", "N/A")
                                    },
                                    "possession": {
                                        "home": stats["home"].get("ball_possession", {}).get("percentage", "N/A"),
                                        "away": stats["away"].get("ball_possession", {}).get("percentage", "N/A")
                                    }
                                }
                    except Exception as e:
                        print(f"❌ Error obteniendo estadísticas para fixture {fixture_id}: {e}")
                    historial[league_id].append(match)
            except Exception as e:
                print(f"❌ Error fetching data for league {league_id}, season {season}: {e}")
    return historial

# Guardar y subir archivos a Google Drive
def update_drive_files(service, folder_id, historial):
    for league_id, matches in historial.items():
        file_name = f"liga_{league_id}.json"
        if matches:  # Solo subir si hay datos
            file_path = f"{file_name}"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(matches, f, ensure_ascii=False, indent=2)
            media = MediaFileUpload(file_path, mimetype='application/json')
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = response.get('files', [])
            file_id = files[0]['id'] if files else None
            if file_id:
                service.files().update(fileId=file_id, media_body=media).execute()
                print(f"Archivo {file_name} sobreescrito en Google Drive.")
            else:
                file_metadata = {'name': file_name, 'parents': [folder_id]}
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"Archivo {file_name} creado en Google Drive.")
    print(f"✅ Actualizados {sum(len(matches) for matches in historial.values())} partidos en total.")

# Ejecución principal
if __name__ == "__main__":
    try:
        service = get_drive_service()
        folder_id = get_or_create_folder(service, FOLDER_NAME)
        historial = fetch_football_data()
        update_drive_files(service, folder_id, historial)
    except Exception as e:
        print(f"❌ Error general: {e}")
        raise
