
# generador_tenis.py

from utils.telegram import enviar_mensaje
from utils.sofascore import obtener_partidos_tenis, analizar_rompimientos
from utils.valor import detectar_valor_tenis
from utils.formato import formatear_pick

def enviar_picks_tenis():
    partidos = obtener_partidos_tenis()

    picks = []
    for partido in partidos:
        analisis = analizar_rompimientos(partido)
        if detectar_valor_tenis(partido, analisis):
            pick_formateado = formatear_pick(partido, analisis, deporte="tenis")
            picks.append(pick_formateado)

    if picks:
        for pick in picks:
            enviar_mensaje("vip", pick)
        enviar_mensaje("vip", f"✅ {len(picks)} picks de TENIS enviados con valor detectado.")
    else:
        enviar_mensaje("vip", "🚫 No se encontraron picks de TENIS con valor hoy.")
