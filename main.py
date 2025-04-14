from generador_tenis import enviar_picks_tenis
from generador_futbol import enviar_picks_futbol
from generador_mlb import enviar_picks_mlb
from generador_nba import enviar_picks_nba
from generador_parlay import enviar_parlay_diario
from generador_reto import enviar_reto_escalera
from generador_mini_reto import enviar_mini_reto_escalera

import schedule
import time

# Aquí se ejecutan todos los generadores automáticamente
enviar_picks_tenis()
enviar_picks_futbol()
enviar_picks_mlb()
enviar_picks_nba()
enviar_parlay_diario()
enviar_reto_escalera()
enviar_mini_reto_escalera()

# Horarios programados (hora del servidor Railway -6 GMT México)

# 🎾 Tenis a las 22:00
schedule.every().day.at("22:00").do(enviar_picks_tenis)

# ⚽ Fútbol 2 horas antes del primer partido (se ajusta internamente en el script)
schedule.every().day.at("05:00").do(enviar_picks_futbol)

# ⚾ MLB y 🏀 NBA 5 horas antes del primer partido (se ajusta internamente en el script)
schedule.every().day.at("06:00").do(enviar_picks_mlb)
schedule.every().day.at("06:00").do(enviar_picks_nba)

# 🔒 Reto Escalera 5 horas antes del mejor pick
schedule.every().day.at("06:00").do(enviar_reto_escalera)

# ⭐ Parlay diario combinado
schedule.every().day.at("09:00").do(enviar_parlay_diario)

# 🪜 Mini Reto Free (solo cada 2 semanas, validación interna)
schedule.every().day.at("09:10").do(enviar_mini_reto_escalera)

print("✅ Sistema DG Picks Automático Iniciado")

while True:
    schedule.run_pending()
    time.sleep(30)
