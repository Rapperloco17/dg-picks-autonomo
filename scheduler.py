import schedule
import time
import os

from soccer_generator import generate_soccer_picks
from top_matches import generar_top5


def schedule_soccer_analysis():
    schedule.every().day.at("11:15").do(generate_soccer_picks)
    schedule.every().day.at("10:10").do(generar_top5)
    print("⚽ Análisis de fútbol programado a las 11:15 a.m. y Top 5 a las 10:10 a.m. (hora local del servidor)")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    schedule_soccer_analysis()
