
# generador_reto.py

from utils.telegram import enviar_mensaje_reto
from utils.reto_stats import obtener_picks_reto, seleccionar_mas_seguro
from utils.formato import formatear_pick

def enviar_pick_reto_escalera():
    picks = obtener_picks_reto()

    if not picks:
        enviar_mensaje_reto("🚫 No se encontraron picks adecuados para el Reto Escalera hoy.")
        return

    pick = seleccionar_mas_seguro(picks)

    if pick:
        pick_formateado = formatear_pick(pick, pick['analisis'], reto_escalera=True)
        enviar_mensaje_reto("🔒 *Reto Escalera – Pick del Día* 🔒")
        enviar_mensaje_reto(pick_formateado)
    else:
        enviar_mensaje_reto("⚠️ No se pudo seleccionar un pick seguro para el Reto Escalera hoy.")
