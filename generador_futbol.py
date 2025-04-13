from utils.sofascore import obtener_partidos_futbol
from utils.telegram import log_envío
from utils.valor_cuota import detectar_valor_futbol

def enviar_picks_futbol():
    print("📊 Inicio de análisis de Fútbol...")
    partidos = obtener_partidos_futbol()

    for partido in partidos:
        if detectar_valor_futbol(partido["cuota"]):
            mensaje = f"⚽ Pick Fútbol\n{partido['equipo_local']} vs {partido['equipo_visitante']}\nCuota: {partido['cuota']}"
            log_envío(mensaje)

    print("✅ Picks de Fútbol enviados.")

