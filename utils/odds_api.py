# utils/odds_api.py

from utils.cuotas import obtener_cuota_bet365

def get_odds_for_match(match):
    """
    Retorna la cuota de Bet365 para un partido específico.
    Actualmente solo simula obteniendo el deporte y usa la función real.
    """
    deporte = match.get("deporte", "futbol")  # por defecto asumimos que es fútbol
    mercado = "h2h"  # mercado Money Line

    cuota = obtener_cuota_bet365(deporte, mercado)
    return cuota
