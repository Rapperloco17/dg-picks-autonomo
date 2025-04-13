from generador_tenis import enviar_picks_tenis
from generador_mlb import enviar_picks_mlb
from generador_nba import enviar_picks_nba
from generador_futbol import enviar_picks_futbol

def enviar_parlay_diario(es_bomba=False):
    print("💥 Generando Parlay Diario...")

    enviar_picks_tenis()
    enviar_picks_mlb()
    enviar_picks_nba()
    enviar_picks_futbol()

    if es_bomba:
        print("🚀 Este parlay se marcará como BOMBA por su cuota alta.")

    print("✅ Parlay diario generado.")
