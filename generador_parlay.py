# generador_parlay.py

from generator_tenis import enviar_picks_tenis
from generator_mlb import enviar_picks_mlb
from generator_nba import enviar_picks_nba
from generator_futbol import enviar_picks_futbol

def enviar_parlay_diario(es_bomba=False):
    # Ejecuta los generadores por separado, pero solo recopila los picks (sin enviar duplicado)
    enviar_picks_tenis()
    enviar_picks_mlb()
    enviar_picks_nba()
    enviar_picks_futbol()
    
    # El formato y envío ya están contenidos en cada generador
    # Este archivo se asegura de que todos corran juntos como parte del parlay del día o bomba legendaria si es finde
    if es_bomba:
        print("[BOMBA] Se ejecutó como Bomba Legendaria (cuota +150)")
    else:
        print("[PARLAY] Se ejecutó Parlay Combinado Diario")
