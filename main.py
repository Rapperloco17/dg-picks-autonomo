import schedule
import time
from generadores.generador_tenis import generar_picks_tenis
from generadores.generador_futbol import generar_picks_futbol
from generadores.generador_mlb import generar_picks_mlb
from generadores.generador_nba import generar_picks_nba
from generadores.generador_reto import generar_pick_reto
from generadores.generador_parlay import generar_parlay_diario

# Funciones programadas por horario

def tenis_job():
    print("\n🎾 Ejecutando picks de tenis...")
    generar_picks_tenis()

def futbol_job():
    print("\n⚽ Ejecutando picks de fútbol...")
    generar_picks_futbol()

def mlb_job():
    print("\n⚾ Ejecutando picks de MLB...")
    generar_picks_mlb()

def nba_job():
    print("\n🏀 Ejecutando picks de NBA...")
    generar_picks_nba()

def reto_job():
    print("\n🧱 Ejecutando pick del Reto Escalera...")
    generar_pick_reto()

def parlay_job():
    print("\n💥 Ejecutando parlay del día...")
    generar_parlay_diario()

# Horarios programados
schedule.every().day.at("22:00").do(tenis_job)  # Tenis a las 10:00 p.m.
schedule.every().day.at("07:00").do(futbol_job) # Fútbol 2 horas antes, ajustable según horario real
schedule.every().day.at("06:00").do(mlb_job)    # MLB 5 horas antes
schedule.every().day.at("06:00").do(nba_job)    # NBA 5 horas antes
schedule.every().day.at("06:00").do(reto_job)   # Reto Escalera 5 horas antes
schedule.every().day.at("08:00").do(parlay_job) # Parlay diario

print("✅ DG Picks está en modo automático. Esperando horarios...")

while True:
    schedule.run_pending()
    time.sleep(30)
