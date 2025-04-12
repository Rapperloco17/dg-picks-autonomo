from utils.sofascore import obtener_partidos_tenis, analizar_rompimientos
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from utils.cuotas_cache import get_cuota_cached
from utils.valor import validar_valor_cuota

def enviar_picks_tenis():
    partidos = obtener_partidos_tenis()
    picks_validados = []

    for partido in partidos:
        jugador1 = partido["jugador1"]
        jugador2 = partido["jugador2"]
        enfrentamiento = f"{jugador1} vs {jugador2}"

        cuota = get_cuota_cached(enfrentamiento, "h2h", "tenis")
        if not validar_valor_cuota(cuota):
            continue

        analisis = analizar_rompimientos(partido)
        analisis["descripcion"] += f" Cuota: @{cuota}"

        texto = formatear_pick(partido, analisis, deporte="Tenis")
        picks_validados.append(texto)

    if picks_validados:
        parlay_texto = "\n\n".join(picks_validados)
        parlay_texto = f"🎾 PARLAY TENIS DEL DÍA 🎾\n\n{parlay_texto}"
        enviar_mensaje("VIP", parlay_texto)

