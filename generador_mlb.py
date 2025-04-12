# generador_mlb.py

from utils.mlb_stats import obtener_partidos_mlb, analizar_pitchers
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from utils.cuotas_cache import get_cuota_cached
from utils.cuotas import validar_valor_cuota

def enviar_picks_mlb():
    partidos = obtener_partidos_mlb()
    picks_validados = []

    for partido in partidos:
        equipo1 = partido["equipo1"]
        equipo2 = partido["equipo2"]
        enfrentamiento = f"{equipo1} vs {equipo2}"

        cuota = get_cuota_cached(enfrentamiento, "h2h", "mlb")
        if not validar_valor_cuota(cuota):
            continue  # Saltar pick si no tiene valor real

        analisis = analizar_pitchers(partido)
        analisis["descripcion"] += f" Cuota: @{cuota}"

        texto = formatear_pick(partido, analisis, deporte="MLB")
        picks_validados.append(texto)

    if picks_validados:
        parlay_texto = "\n\n".join(picks_validados)
        parlay_texto = f"🔥 PARLAY MLB DEL DÍA 🔥\n\n{parlay_texto}"
        enviar_mensaje("VIP", parlay_texto)
