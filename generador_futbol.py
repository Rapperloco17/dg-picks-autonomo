# generador_futbol.py

from utils.soccer_stats import obtener_partidos_futbol, analizar_equipo
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from utils.cuotas_cache import get_cuota_cached
from utils.cuotas import validar_valor_cuota

def enviar_picks_futbol():
    partidos = obtener_partidos_futbol()
    picks_validados = []

    for partido in partidos:
        equipo1 = partido["equipo1"]
        equipo2 = partido["equipo2"]
        enfrentamiento = f"{equipo1} vs {equipo2}"

        cuota = get_cuota_cached(enfrentamiento, "h2h", "futbol")
        if not validar_valor_cuota(cuota, min_valor=1.50, max_valor=3.50):
            continue  # Saltar pick si la cuota no tiene valor real

        analisis = analizar_equipo(partido)
        analisis["descripcion"] += f" Cuota: @{cuota}"

        texto = formatear_pick(partido, analisis, deporte="Fútbol")
        picks_validados.append(texto)

    if picks_validados:
        parlay_texto = "\n\n".join(picks_validados)
        parlay_texto = f"⚽ PARLAY DE FÚTBOL DEL DÍA ⚽\n\n{parlay_texto}"
        enviar_mensaje("VIP", parlay_texto)
