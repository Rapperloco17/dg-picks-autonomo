from utils.sofascore import obtener_partidos_nba
from utils.telegram import log_envío
from utils.valor_cuota import detectar_valor_nba

def enviar_picks_nba():
    print("📊 Inicio de análisis de NBA...")
    partidos = obtener_partidos_nba()

    for partido in partidos:
        if detectar_valor_nba(partido["cuota"]):
            mensaje = f"🏀 Pick NBA\n{partido['equipo_local']} vs {partido['equipo_visitante']}\nCuota: {partido['cuota']}"
            log_envio(mensaje)

    print("✅ Picks de NBA enviados.")
