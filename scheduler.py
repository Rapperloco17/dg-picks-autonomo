def schedule_soccer_analysis():
    schedule.every().day.at("06:15").do(generate_soccer_picks)   # nuevo horario para los picks
    schedule.every().day.at("10:10").do(generar_top5)             # se mantiene igual el Top 5

    print("⚽ Análisis de fútbol programado a las 06:15 a.m. y Top 5 a las 10:10 a.m. (hora local del servidor)")

    while True:
        schedule.run_pending()
        time.sleep(60)
