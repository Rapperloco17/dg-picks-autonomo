import datetime

def analizar_partido_profundo(fixture, stats, prediction):
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
            return next((x['value'] for x in stat_list if x.get('type') == stat_type), 0) or 0
        except:
            return 0

    try:
        home_stats_list = stats.get('home', {}).get('statistics', [])
        away_stats_list = stats.get('away', {}).get('statistics', [])

        if not isinstance(home_stats_list, list) or not isinstance(away_stats_list, list):
            raise ValueError("Formato inesperado en estadísticas")

        home_goals = get_stat(home_stats_list, "Goals scored")
        away_goals = get_stat(away_stats_list, "Goals scored")

        home_concede = get_stat(home_stats_list, "Goals conceded")
        away_concede = get_stat(away_stats_list, "Goals conceded")

        # Lógica de generación
        if home_goals + away_goals >= 3 and home_concede + away_concede >= 2:
            razonamiento.append(f"📈 Ambos equipos promedian muchos goles: {home_goals}+{away_goals} anotados y {home_concede}+{away_concede} concedidos.")
            pick = "Over 2.5 goles"

        elif home_goals >= 1.5 and away_concede >= 1.2:
            razonamiento.append(f"⚽ El local ({home}) anota bastante y el visitante ({away}) concede muchos.")
            pick = f"{home} gana o Over 1.5 goles"

        elif home_concede >= 1.5 and away_goals >= 1.3:
            razonamiento.append(f"🚨 El visitante ({away}) suele anotar y el local ({home}) recibe goles.")
            pick = "Ambos anotan (BTTS)"

        if pick and advice and pick.lower() in advice.lower():
            razonamiento.append(f"✅ El consejo del API también recomienda: {advice}")
        elif pick:
            razonamiento.append("⚠️ Pick generado por estadísticas, no coincide 100% con el consejo del API.")

    except Exception as e:
        print(f"❌ Error en análisis profundo del fixture {fixture_id}: {e}")
        return None

    if not pick:
        return None

    return {
        "fixture_id": fixture_id,
        "match": f"{home} vs {away}",
        "league": league,
        "date": date,
        "pick": pick,
        "razonamiento": razonamiento
    }


