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
    enfrentamiento = f"{jugador1} vs {
