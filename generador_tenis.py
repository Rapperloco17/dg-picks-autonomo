from utils.sofascore import obtener_partidos_tenis, analizar_rompimientos
from utils.telegram import log_envío
from utils.valor_cuota import (
    detectar_valor_tenis,
    detectar_valor_mlb,
    detectar_valor_nba,
    detectar_valor_futbol
)

def enviar_picks_tenis():
    print("⏳ Inicio de análisis de tenis...")
    partidos = obtener_partidos_tenis()

    for partido in partidos:
        if detectar_valor_tenis(partido["cuota"]):
            análisis = analizar_rompimientos(partido)
            mensaje = f"🎾 *Pick de Tenis*\n\n{análisis}"
            log_envío(mensaje)

    print("✅ Picks de tenis enviados.")

