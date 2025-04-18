import schedule
import time
import os

from soccer_generator import generate_soccer_picks
from top_matches import generate_top5

def schedule_soccer_analysis():
    schedule.every().day.at("04:30").do(generate_soccer_picks)
    schedule.every().day.at("10:10").do(generate_top5)
    print("⚽ Análisis de fútbol programado a las 04:30 a.m. y Top 5 a las 10:10 a.m. (hora local del servidor)")

    while True:
        schedule.run_pending()
        time.sleep(60)

schedule_soccer_analysis()
