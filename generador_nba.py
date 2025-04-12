# generador_nba.py

from utils.nba_stats import obtener_partidos_nba, analizar_nba
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from utils.cuotas_cache import get_cuota_cached
from utils.cuotas import validar_valor_cuota

def enviar_picks_nba():
    partidos = obtener_partidos_nba()
    picks_validados = []

    for partido in partidos:
        equipo1 = partido["equipo1"]
        equipo2 = partido["equipo2"]
        enfrentamiento = f"{equipo1} vs {equipo2}"

        cuota = get_cuota_cached(enfrentamiento, "h2h", "nba")
        if not validar_valor_cuota(cuota):
            continue  # Saltar pick si la cuota no tiene valor

        analisis = analizar_nba(partido)
        analisis["descripcion"] += f" Cuota: @{cuota}"

        texto = formatear_pick(partido, analisis, deporte="NBA")
        picks_validados.append(texto)

    if picks_validados:
        parlay_texto = "\n\n".join(picks_validados)
        parlay_texto = f"🔥 PARLAY NBA DEL DÍA 🔥\n\n{parlay_texto}"
        enviar_mensaje("VIP", parlay_texto)
