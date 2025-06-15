import requests
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime

# Configuración
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDS_CONTENT = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
if CREDS_CONTENT:
    creds_info = json.loads(CREDS_CONTENT)
    with open('temp_credentials.json', 'w') as f:
        json.dump(creds_info, f)
    CREDS_FILE = 'temp_credentials.json'
else:
    CREDS_FILE = 'credentials.json'

FOLDER_NAME = 'historial_fusionado'
API_KEY = os.environ.get("API_FOOTBALL_KEY")
if not API_KEY:
    print("❌ Error: API_FOOTBALL_KEY no está definida en las variables de entorno.")
    raise ValueError("API_FOOTBALL_KEY no configurada")
else:
    print(f"✅ API_KEY detectada: {API_KEY[:5]}... (ocultada por seguridad)")
HEADERS = {"x-apisports-key": API_KEY}
print(f"🔍 Headers enviados: {HEADERS}")
LIGAS_ASIGNADAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

# Fecha actual para filtrar
current_date = datetime.now().strftime('%Y-%m-%d')

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = service_account.Credentials.from_service_account_file('token.json', scopes=SCOPES)
    if not creds or not creds.valid:
        try:
            creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        except Exception as e:
            print(f"❌ Error en autenticación de Google Drive: {e}")
            raise
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    if folders:
        return folders[0]['id']
    folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def parse_statistics(stats_list):
    stats = {}
    for item in stats_list:
        stat_type = item.get('type', 'unknown')
        value = item.get('value', None)
        if isinstance(value, (int, float, str)) or value is None:
            stats[stat_type] = value
        elif isinstance(value, list):
            stats[stat_type] = [v for v in value if v is not None]
    return stats

def fetch_football_data():
    historial = {}
    seasons = [2024, 2025]
    start_date = '2024-01-01'  # Inicio de 2024
    for season in seasons:
        for league_id in LIGAS_ASIGNADAS:
            historial[league_id] = []
            page = 1
            max_pages = 50  # Límite razonable
            while page <= max_pages:
                url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}&page={page}&from={start_date}&to={current_date}"
                print(f"🔎 Consultando: {url}")
                try:
                    response = requests.get(url, headers=HEADERS, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    fixtures = data.get('response', [])
                    paging = data.get('paging', {})
                    total_pages = paging.get('total', 1)
                    print(f"📊 Liga {league_id}, temporada {season}, página {page}/{total_pages} - {len(fixtures)} partidos")
                    if not fixtures or page >= total_pages:
                        if not fixtures:
                            print(f"⚠️ Sin fixtures disponibles para liga {league_id}, temporada {season} entre {start_date} y {current_date}")
                        break
                    for fixture in fixtures:
                        fixture_id = fixture['fixture']['id']
                        print(f"📋 Procesando fixture {fixture_id} - Fecha: {fixture['fixture'].get('date', 'N/A')}")
                        match = {
                            "teams": {
                                "home": {"name": fixture['teams']['home'].get('name', 'Unknown')},
                                "away": {"name": fixture['teams']['away'].get('name', 'Unknown')}
                            },
                            "goals": {
                                "home": fixture['goals'].get('home', 0) or 0,
                                "away": fixture['goals'].get('away', 0) or 0
                            },
                            "league": {"id": league_id, "name": fixture['league'].get('name', 'Unknown')},
                            "fixture": {
                                "date": fixture['fixture'].get('date', 'N/A'),
                                "status": fixture['fixture'].get('status', 'N/A')
                            }
                        }
                        try:
                            r_stats = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}", headers=HEADERS, timeout=10)
                            r_stats.raise_for_status()
                            stats_data = r_stats.json().get("response", [])
                            if stats_data:
                                stats = {}
                                for team_stats in stats_data:
                                    team_name = team_stats["team"].get("name", "Unknown")
                                    parsed = parse_statistics(team_stats.get("statistics", []))
                                    if team_name == match["teams"]["home"]["name"]:
                                        stats["home"] = parsed
                                    elif team_name == match["teams"]["away"]["name"]:
                                        stats["away"] = parsed
                                if stats:
                                    match["stats"] = stats
                                else:
                                    print(f"⚠️ Sin estadísticas válidas para fixture {fixture_id}")
                            else:
                                print(f"⚠️ Respuesta vacía de estadísticas para fixture {fixture_id}")
                        except requests.exceptions.RequestException as e:
                            print(f"❌ Error obteniendo estadísticas para fixture {fixture_id}: {str(e)} - Status Code: {getattr(e.response, 'status_code', 'N/A')}")
                        historial[league_id].append(match)
                    page += 1
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error en liga {league_id}, temporada {season}: {str(e)} - Status Code: {getattr(e.response, 'status_code', 'N/A')}")
                    break
            print(f"✅ Total de partidos encontrados para liga {league_id}, temporada {season}: {len(historial[league_id])}\n")
    return historial

def update_drive_files(service, folder_id, historial):
    for league_id, matches in historial.items():
        file_name = f"liga_{league_id}.json"
        if matches:
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
                print(f"🔁 Archivo {file_name} sobreescrito en Drive.")
            else:
                file_metadata = {'name': file_name, 'parents': [folder_id]}
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"🆕 Archivo {file_name} creado en Drive.")
            os.remove(file_path)
    print(f"✅ Total actualizado: {sum(len(m) for m in historial.values())} partidos.")

if __name__ == "__main__":
    try:
        service = get_drive_service()
        folder_id = get_or_create_folder(service, FOLDER_NAME)
        historial = fetch_football_data()
        update_drive_files(service, folder_id, historial)
    except Exception as e:
        print(f"❌ Error general: {e}")
        raise
