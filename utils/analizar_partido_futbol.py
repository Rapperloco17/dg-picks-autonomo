# utils/analizar_partido_futbol.py

def analizar_partido_futbol(partido, datos_estadisticos, cuotas):
    """
    Análisis real del partido basado en datos estadísticos y cuotas.
    Esta es una versión inicial que puedes extender.

    :param partido: dict con datos del fixture
    :param datos_estadisticos: dict con estadísticas detalladas del partido
    :param cuotas: dict con cuotas disponibles del partido
    :return: dict con pick sugerido o None si no hay valor
    """

    fixture_id = partido.get("fixture", {}).get("id")
    print(f"🔍 Analizando fixture ID: {fixture_id}")

    # Extraer estadísticas clave
    goles_prom_home = datos_estadisticos.get("home", {}).get("goals_per_game", 0)
    goles_prom_away = datos_estadisticos.get("away", {}).get("goals_per_game", 0)
    btts_ratio = datos_estadisticos.get("btts_ratio", 0)

    # Extraer cuotas
    cuota_over_2_5 = cuotas.get("Over 2.5", 0)
    cuota_btts = cuotas.get("BTTS", 0)

    # Lógica de ejemplo: apostar al Over 2.5 si hay valor
    if goles_prom_home + goles_prom_away >= 2.8 and cuota_over_2_5 >= 1.70:
        return {
            "pick": "Over 2.5 goles",
            "valor": True,
            "motivo": f"Promedio de goles alto ({goles_prom_home + goles_prom_away}), cuota: {cuota_over_2_5}"
        }

    # Lógica de ejemplo: apostar al BTTS si hay valor
    if btts_ratio >= 0.65 and cuota_btts >= 1.80:
        return {
            "pick": "Ambos anotan (BTTS)",
            "valor": True,
            "motivo": f"Alta probabilidad de BTTS ({btts_ratio}), cuota: {cuota_btts}"
        }

    # Si no se cumple nada
    return {
        "pick": None,
        "valor": False,
        "motivo": "No se encontró valor en este partido"
    }
