from utils.sofascore import obtener_partidos_mlb
from utils.telegram import log_envio
from utils.valor_cuota import detectar_valor_mlb

def enviar_picks_mlb():
    print("⚾ Inicio de análisis de MLB...")
    partidos = obtener_partidos_mlb()

    for partido in partidos:
        if detectar_valor_mlb(partido["cuota"]):
            mensaje = f"⚾ Pick MLB\n{partido['equipo_local']} vs {partido['equipo_visitante']}\nCuota: {partido['cuota']}"
            log_envio(mensaje)

    print("✅ Picks de MLB enviados.")
