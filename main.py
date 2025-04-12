import schedule
import time

from generador_tenis import enviar_picks_tenis
from generador_mlb import enviar_picks_mlb
from generador_nba import enviar_picks_nba
from generador_futbol import enviar_picks_futbol
from generador_parlay import enviar_parlay_diario
from generador_reto import enviar_pick_reto_escalera
from generador_mini_reto import enviar_mini_reto_free

from utils.telegram import log_envio
from utils.horarios import obtener_hora_mlb, obtener_hora_nba, obtener_hora_futbol, dia_es_finde, cada_dos_semanas

# 🗓 Programar envíos automáticos por deporte
schedule.every().day.at("22:00").do(enviar_picks_tenis)
schedule.every().day.at(obtener_hora_mlb()).do(enviar_picks_mlb)
schedule.every().day.at(obtener_hora_nba()).do(enviar_picks_nba)
schedule.every().day.at(obtener_hora_futbol()).do(enviar_picks_futbol)

# 📦 Parlay diario (puede ser combinado)
schedule.every().day.at("22:30").do(enviar_parlay_diario)

# 🧗‍♂️ Reto Escalera: pick diario automático 5h antes del juego
schedule.every().day.at("12:00").do(enviar_pick_reto_escalera)

# 🌱 Mini Reto Escalera en canal Free cada 2 semanas (4 pasos)
schedule.every().monday.at("11:00").do(lambda: enviar_mini_reto_free() if cada_dos_semanas() else None)

# 💣 Bomba Legendaria fin de semana (cuota @150+)
def intento_bomba_findes():
    if dia_es_finde():
        enviar_parlay_diario(es_bomba=True)

schedule.every().day.at("13:00").do(intento_bomba_findes)

# 🔁 Loop que ejecuta el sistema
while True:
    schedule.run_pending()
    time.sleep(30)
