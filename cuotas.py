
# utils/cuotas.py

def obtener_cuota_bet365(evento, mercado):
    """
    Simula la obtención de una cuota para un evento desde Bet365.
    :param evento: str - nombre del evento o enfrentamiento
    :param mercado: str - tipo de mercado (ej: ML, over/under)
    :return: float - cuota simulada
    """
    cuotas_simuladas = {
        "ML": 1.85,
        "OVER_2.5": 2.05,
        "HANDICAP": 1.90,
        "PROP_PLAYER": 2.15
    }
    return cuotas_simuladas.get(mercado.upper(), 1.50)

def validar_valor_cuota(cuota, min_valor=1.70, max_valor=2.20):
    """
    Valida si una cuota tiene valor real según los rangos definidos.
    """
    return min_valor <= cuota <= max_valor
