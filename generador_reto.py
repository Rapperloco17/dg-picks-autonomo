# generador_reto.py

from utils.reto_stats import obtener_picks_reto, seleccionar_mas_seguro
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje_reto
from utils.cuotas_cache import get_cuota_cached
from utils.valor_cuota import validar_valor_cuota

def enviar_pick_reto_escalera():
    picks = obtener_picks_reto()

    if not picks:
        enviar_mensaje_reto("🚫 No se encontraron picks adecuados para el Reto Escalera hoy.")
        return

    pick = seleccionar_mas_seguro(picks)
    if not pick:
        enviar_mensaje_reto("⚠️ No se pudo seleccionar un pick seguro para el Reto Escalera hoy.")
        return

    jugador1 = pick.get("jugador1", "Jugador A")
    jugador2 = pick.get("jugador2", "Jugador B")
    enfrentamiento = f"{jugador1} vs {jugador2}"

    cuota = get_cuota_cached(enfrentamiento, "h2h", pick.get("deporte", "tenis"))
    if not validar_valor_cuota(cuota, min_valor=1.50, max_valor=3.50):
        enviar_mensaje_reto("🚫 El pick más seguro no tiene cuota válida para el Reto Escalera.")
        return

    pick["analisis"]["descripcion"] += f" Cuota: @{cuota}"
    pick_formateado = formatear_pick(pick, pick["analisis"], reto_escalera=True)

    enviar_mensaje_reto("🔒 *Reto Escalera – Pick del Día* 🔒")
    enviar_mensaje_reto(pick_formateado)
