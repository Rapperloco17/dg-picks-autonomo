# generador_tenis.py

from utils.sofascore import obtener_partidos_tenis, analizar_rompimientos
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from utils.cuotas_cache import get_cuota_cached
from utils.cuotas import validar_valor_cuota

def enviar_picks_tenis():
    partidos = obtener_partidos_tenis()
    picks_validados = []

    for partido in partidos:
        jugador1 = partido["jugador1"]
        jugador2 = partido["jugador2"]
        enfrentamiento = f"{jugador1} vs {jugador2}"

        # Obtener cuota real desde Bet365 usando cache
        cuota = get_cuota_cached(enfrentamiento, "h2h", "tenis")

        # Validar que la cuota tenga valor (entre 1.50 y 3.50)
        if not validar_valor_cuota(cuota, min_valor=1.50, max_valor=3.50):
            continue  # Saltar si no cumple con el rango de valor permitido

        # Análisis real del partido (enfocado en rompimientos y debilidades)
        analisis = analizar_rompimientos(partido)
        analisis["descripcion"] += f" Cuota: @{cuota}"

        # Formatear el pick listo para envío
        texto = formatear_pick(partido, analisis, deporte="Tenis")
        picks_validados.append(texto)

    # Enviar todos los picks validados como parlay o lista
    if picks_validados:
        parlay_texto = "\n\n".join(picks_validados)
        parlay_texto = f"🎾 PARLAY DE TENIS DEL DÍA 🎾\n\n{parlay_texto}"
        enviar_mensaje("VIP", parlay_texto)
