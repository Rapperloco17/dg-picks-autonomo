import schedule
import time

# 📦 Generadores
from generador_tenis import enviar_picks_tenis
from generador_mlb import enviar_picks_mlb
from generador_nba import enviar_picks_nba
from generador_futbol import enviar_picks_futbol
from generador_parlay import enviar_parlay_diario

# 🔧 Utilidades
from utils.telegram import log_envío
from utils.horarios import (
    obtener_hora_mlb,
    obtener_hora_nba,
    obtener_hora_futbol,
    dia_es_finde,
    cada_dos_semanas
)

# 🕒 Programación diaria
schedule.every().day.at("22:00").do(enviar_picks_tenis)
schedule.every().day.at(obtener_hora_mlb()).do(enviar_picks_mlb)
schedule.every().day.at(obtener_hora_nba()).do(enviar_picks_nba)
schedule.every().day.at(obtener_hora_futbol()).do(enviar_picks_futbol)
schedule.every().day.at("22:30").do(enviar_parlay_diario)

# 💣 Bomba de fin de semana
def intento_bomba_findes():
    if dia_es_finde():
        enviar_parlay_diario(es_bomba=True)

schedule.every().day.at("13:00").do(intento_bomba_findes)

# ♻️ Loop infinito del sistema
while True:
    schedule.run_pending()
    time.sleep(30)
