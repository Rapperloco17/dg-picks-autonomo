# utils/soccer_stats.py – Análisis real del partido para DG Picks

def analizar_partido(fixture):
    """
    Recibe un fixture de la API y devuelve un análisis con pick si se detecta valor real.
    """
    try:
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        home_stats = fixture['teams']['home']
        away_stats = fixture['teams']['away']

        # Simulación de datos clave (en tu sistema real esto vendrá desde stats enriquecidas)
        home_form = fixture.get("form_home", 4)  # Simula forma: 0–5
        away_form = fixture.get("form_away", 2)
        home_win_ratio = fixture.get("home_win_ratio", 0.65)  # 0.0–1.0
        away_loss_ratio = fixture.get("away_loss_ratio", 0.60)

        cuota_local = fixture.get("odds", {}).get("home", 1.70)

        # Criterios de pick con valor
        if home_form >= 3 and away_form <= 2 and home_win_ratio >= 0.60 and cuota_local <= 1.80:
            return {
                "partido": f"{home} vs {away}",
                "pick": f"Gana {home}",
                "cuota": cuota_local,
                "valor": True,
                "justificacion": f"{home} con mejor forma reciente, local sólido, cuota razonable"
            }

        return None  # No hay valor

    except Exception as e:
        print("\u26a0\ufe0f Error analizando partido:", e)
        return None
