
# generador_nba.py

from utils.telegram import enviar_mensaje
from utils.nba_stats import obtener_partidos_nba, analizar_informacion_jugadores
from utils.valor import detectar_valor_nba
from utils.formato import formatear_pick

def enviar_picks_nba():
    partidos = obtener_partidos_nba()

    picks = []
    for partido in partidos:
        analisis = analizar_informacion_jugadores(partido)
        if detectar_valor_nba(partido, analisis):
            pick_formateado = formatear_pick(partido, analisis, deporte="nba")
            picks.append(pick_formateado)

    if picks:
        for pick in picks:
            enviar_mensaje("vip", pick)
        enviar_mensaje("vip", f"✅ {len(picks)} picks de NBA enviados con valor detectado.")
    else:
        enviar_mensaje("vip", "🚫 No se encontraron picks de NBA con valor hoy.")
