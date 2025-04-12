
# generador_mlb.py

from utils.telegram import enviar_mensaje
from utils.mlb_stats import obtener_partidos_mlb, analizar_pitchers
from utils.valor import detectar_valor_mlb
from utils.formato import formatear_pick

def enviar_picks_mlb():
    partidos = obtener_partidos_mlb()

    picks = []
    for partido in partidos:
        analisis = analizar_pitchers(partido)
        if detectar_valor_mlb(partido, analisis):
            pick_formateado = formatear_pick(partido, analisis, deporte="mlb")
            picks.append(pick_formateado)

    if picks:
        for pick in picks:
            enviar_mensaje("vip", pick)
        enviar_mensaje("vip", f"✅ {len(picks)} picks de MLB enviados con valor detectado.")
    else:
        enviar_mensaje("vip", "🚫 No se encontraron picks de MLB con valor hoy.")
