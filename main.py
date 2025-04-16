from generador_tenis import enviar_picks_tenis
from generador_reto import enviar_reto_escalera
from generador_mini_reto import enviar_mini_reto_escalera

import schedule
import time

# 🕒 Horarios programados (hora del servidor Railway -6 GMT México)

# 🎾 Tenis a las 22:00
schedule.every().day.at("22:00").do(enviar_picks_tenis)

# 🏆 Reto Escalera - 5 horas antes del mejor pick
schedule.every().day.at("06:00").do(enviar_reto_escalera)

# 🏅 Mini Reto Free (cada 2 semanas)
schedule.every().day.at("09:10").do(enviar_mini_reto_escalera)

print("✅ Sistema DG Picks Automático Iniciado")

while True:
    schedule.run_pending()
    time.sleep(30)
