import schedule
import time

# 📦 Importar funciones de generación por deporte
from generador_tenis import enviar_picks_tenis
from generador_mlb import enviar_picks_mlb
from generador_nba import enviar_picks_nba
from generador_futbol import enviar_picks_futbol
from generador_parlay import enviar_parlay_diario
from generador_reto import enviar_pick_reto_escalera
from generador_mini_reto import enviar_mini_reto_free

# 🧰 Importar utilidades
from utils.telegram import log_envio
from utils.horarios import (
    obtener_hora_mlb,
    obtener_hora_nba,
    obtener_hora_futbol,
    dia_es_finde,
    cada_dos_semanas
)

from utils.valor_cuota import (
    detectar_valor_tenis,
    detectar_valor_mlb,
    detectar_valor_nba,
    detectar_valor_futbol
)

# 🕓 Envíos automáticos por deporte
schedule.every().day.at("22:00").do(enviar_picks_tenis)
schedule.every().day.at(obtener_hora_mlb()).do(enviar_picks_mlb)
schedule.every().day.at(obtener_hora_nba()).do(enviar_picks_nba)
schedule.every().day.at(obtener_hora_futbol()).do(enviar_picks_futbol)

# 🔁 Parlay diario combinado
schedule.every().day.at("22:30").do(enviar_parlay_diario)

# 🔒 Reto Escalera (enviar pick 5 hrs antes del juego)
schedule.every().day.at("12:00").do(enviar_pick_reto_escalera)

# 🆓 Mini Reto Escalera Free (cada 2 semanas)
schedule.every().monday.at("11:00").do(enviar_mini_reto_free)

# 🔁 Loop infinito para mantener el script activo
while True:
    schedule.run_pending()
    time.sleep(60)
