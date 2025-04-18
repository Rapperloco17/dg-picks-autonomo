def evaluar_valor_cuota(probabilidad_implied, cuota_real):
    """
    Evalúa si una cuota tiene valor en función de la probabilidad implícita estimada
    y la cuota real ofrecida por la casa de apuestas.

    :param probabilidad_implied: Probabilidad estimada (por ejemplo, 0.60 para 60%)
    :param cuota_real: Cuota decimal ofrecida (por ejemplo, 2.10)
    :return: True si tiene valor esperado positivo, False si no
    """
    if cuota_real <= 1:
        return False

    valor_esperado = (cuota_real * probabilidad_implied) - 1
    return valor_esperado > 0
