def analizar_partido_profundo(fixture, stats, prediction):
    try:
        # Validar que 'stats' y 'prediction' sean diccionarios válidos
        if not isinstance(stats, dict):
            print(f"⚠️ Stats inválidas para fixture {fixture['fixture']['id']}")
            return None
        if not isinstance(prediction, dict):
            print(f"⚠️ Predicción inválida para fixture {fixture['fixture']['id']}")
            return None

        # Continúa con tu lógica normal...
        fixture_id = fixture['fixture']['id']
        date = fixture['fixture']['date'][:10]
        league = fixture['league']['name']
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        advice = prediction.get('advice', '').strip()

        razonamiento = []
        pick = None

        def get_stat(stat_list, stat_type):
            try:
                return next((x['value'] for x in stat_list if x.get('type') == stat_type), 0)
            except:
                return 0

        home_stats_list = stats.get('home', {}).get('statistics', [])
        away_stats_list = stats.get('away', {}).get('statistics', [])

        if not isinstance(home_stats_list, list) or not isinstance(away_stats_list, list):
            raise ValueError("⚠️ Formato inesperado en estadísticas")

        home_goals = get_stat(home_stats_list, "Goals scored")
        away_goals = get_stat(away_stats_list, "Goals scored")
        home_concede = get_stat(home_stats_list, "Goals conceded")
        away_concede = get_stat(away_stats_list, "Goals conceded")

        # Aquí va la lógica de generación de pick...

        # [Tu lógica intacta aquí, según lo que usas]

        return {
            "fixture_id": fixture_id,
            "match": f"{home} vs {away}",
            "league": league,
            "date": date,
            "pick": pick,
            "razonamiento": razonamiento
        }

    except Exception as e:
        print(f"❌ Error en análisis profundo del fixture {fixture['fixture']['id']}: {e}")
        return None
