
# generador_futbol.py

from utils.telegram import enviar_mensaje
from utils.soccer_stats import obtener_partidos_futbol, analizar_equipo_futbol
from utils.valor import detectar_valor_futbol
from utils.formato import formatear_pick

def enviar_picks_futbol():
    partidos = obtener_partidos_futbol()

    picks = []
    for partido in partidos:
        analisis = analizar_equipo_futbol(partido)
        if detectar_valor_futbol(partido, analisis):
            pick_formateado = formatear_pick(partido, analisis, deporte="futbol")
            picks.append(pick_formateado)

    if picks:
        for pick in picks:
            enviar_mensaje("vip", pick)
        enviar_mensaje("vip", f"✅ {len(picks)} picks de FÚTBOL enviados con valor detectado.")
    else:
        enviar_mensaje("vip", "🚫 No se encontraron picks de FÚTBOL con valor hoy.")
