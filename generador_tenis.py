
from utils.sofascore import obtener_partidos_tenis, analizar_rompimientos
from utils.telegram import log_envio
from utils.valor_cuota import detectar_valor_tenis

def enviar_picks_tenis():
    print("🎾 Inicio de análisis de tenis...")
    partidos = obtener_partidos_tenis()

    for partido in partidos:
        if detectar_valor_tenis(partido["cuota"]):
            analisis = analizar_rompimientos(partido)
            mensaje = f"🎾 Pick Tenis\n{analisis}\nCuota: {partido['cuota']}"
            log_envío("vip", mensaje)

    print("✅ Picks de tenis enviados.")
