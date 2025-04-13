
import schedule
import time

from generador_tenis import enviar_picks_tenis
from generador_mlb import enviar_picks_mlb
from generador_nba import enviar_picks_nba
from generador_futbol import enviar_picks_futbol
from generador_parlay import enviar_parlay_diario
from generador_reto import enviar_reto_escalera
from generador_mini_reto import enviar_mini_reto

# Horarios programados (ajustables)
schedule.every().day.at("10:00").do(enviar_picks_tenis)
schedule.every().day.at("14:00").do(enviar_picks_mlb)
schedule.every().day.at("14:00").do(enviar_picks_nba)
schedule.every().day.at("11:00").do(enviar_picks_futbol)
schedule.every().day.at("12:00").do(enviar_parlay_diario)
schedule.every().day.at("13:00").do(enviar_reto_escalera)
schedule.every().day.at("16:00").do(enviar_mini_reto)

# Bucle continuo del sistema
while True:
    schedule.run_pending()
    time.sleep(30)
