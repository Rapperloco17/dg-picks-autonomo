
import requests
import pandas as pd
import os
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7520899056:AAHaS2Id5BGa9HlrX6YWJFX6hCnZsADTOFA"
CHAT_ID = "7450739156"

archivos = ["39.json", "40.json"]
BASE_URL = "https://raw.githubusercontent.com/Rapperloco17/dg-picks-autonomo/main/historial/"

def enviar_excel_telegram(nombre_archivo):
    try:
        file_size = os.path.getsize(nombre_archivo) / (1024 * 1024)  # En MB
        if file_size > 49:
            logger.warning(f"{nombre_archivo} excede el límite de 50 MB ({file_size:.2f} MB)")
            return

        with open(nombre_archivo, "rb") as f:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": CHAT_ID},
                files={"document": (nombre_archivo, f)},
                timeout=30
            )
            if response.status_code == 200:
                logger.info(f"📤 Enviado a Telegram: {nombre_archivo}")
            else:
                logger.error(f"❌ Error al enviar {nombre_archivo}: {response.text}")
    except Exception as e:
        logger.error(f"❌ Error en enviar_excel_telegram: {e}")

for archivo in archivos:
    url = BASE_URL + archivo
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        partidos = data if isinstance(data, list) else data.get("response", [])

        if not partidos:
            logger.warning(f"⚠️ No se encontraron partidos en {archivo}")
            continue

        rows = []
        for partido in partidos:
            fixture = partido.get("fixture", {})
            teams = partido.get("teams", {})
            goals = partido.get("goals", {})
            league = partido.get("league", {})

            row = {
                "Fecha": fixture.get("date", ""),
                "Liga": league.get("name", ""),
                "Local": teams.get("home", {}).get("name", ""),
                "Visitante": teams.get("away", {}).get("name", ""),
                "Goles Local": goals.get("home", ""),
                "Goles Visitante": goals.get("away", ""),
                "Estado": fixture.get("status", {}).get("short", "")
            }

            # Extraer estadísticas si existen
            estadisticas = partido.get("estadisticas", [])
            for equipo_stats in estadisticas:
                team_name = equipo_stats.get("team", {}).get("name", "")
                prefix = "Local" if team_name == row["Local"] else "Visitante"
                for stat in equipo_stats.get("statistics", []):
                    tipo = stat.get("type", "").strip()
                    valor = stat.get("value", "")
                    columna = f"{prefix} - {tipo}"
                    row[columna] = valor

            rows.append(row)

        df = pd.DataFrame(rows)
        nombre_excel = archivo.replace(".json", ".xlsx")
        df.to_excel(nombre_excel, index=False)
        logger.info(f"✅ Excel generado: {nombre_excel}")
        enviar_excel_telegram(nombre_excel)

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error al leer {archivo}: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado con {archivo}: {e}")
