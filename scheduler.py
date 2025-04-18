import schedule
import time
import subprocess
from datetime import datetime

def job_futbol():
    print("⚽ Ejecutando análisis de fútbol diario...")
    subprocess.run(["python", "soccer_generator.py"])

def job_top5():
    print("🔥 Ejecutando TOP 5 de picks...")
    subprocess.run(["python", "top_matches.py"])

# Ejecuta análisis general de fútbol a las 6:15 AM
schedule.every().day.at("06:15").do(job_futbol)

# Ejecuta Top 5 a las 11:15 AM
schedule.every(1).minutes.do(job_top5)


print("📅 Análisis de fútbol programado a las 06:15 a.m. y Top 5 a las 11:15 a.m. (hora local del servidor)")

while True:
    schedule.run_pending()
    time.sleep(30)  # verifica cada 30 segundos
