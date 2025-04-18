import schedule
import time
import os
from soccer_generator import generate_soccer_picks

def schedule_soccer_analysis():
    schedule.every().day.at("04:30").do(generate_soccer_picks)
    print("⏰ Análisis de fútbol programado a las 04:30 a.m. (hora local del servidor)")

    while True:
        schedule.run_pending()
        time.sleep(60)

