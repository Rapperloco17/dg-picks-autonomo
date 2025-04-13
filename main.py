import schedule
import time
from generador_tenis import generar_picks_tenis
from generador_futbol import generar_picks_futbol
from generador_mlb import generar_picks_mlb
from generador_nba import generar_picks_nba
from generador_parlay import generar_parlay_diario
from generador_reto import generar_reto_escalera
from generador_mini_reto import generar_mini_reto_free

# Horarios programados (hora del servidor Railway -6 GMT México)

# Tenis a las 22:00
schedule.every().day.at("22:00").do(generar_picks_tenis)

# Fútbol 2 horas antes del primer partido (se ajusta internamente en el script)
schedule.every().day.at("05:00").do(generar_picks_futbol)

# MLB y NBA 5 horas antes del primer partido (se ajusta internamente en el script)
schedule.every().day.at("06:00").do(generar_picks_mlb)
schedule.every().day.at("06:00").do(generar_picks_nba)

# Reto Escalera 5 horas antes del mejor pick
schedule.every().day.at("06:00").do(generar_reto_escalera)

# Parlay diario combinado
schedule.every().day.at("09:00").do(generar_parlay_diario)

# Mini Reto Free (solo cada 2 semanas, validación interna)
schedule.every().day.at("09:10").do(generar_mini_reto_free)

print("✅ Sistema DG Picks Automático Iniciado")

while True:
    schedule.run_pending()
    time.sleep(30)
