
# generador_mini_reto.py

from utils.telegram import enviar_mensaje_free
from utils.reto_stats import obtener_picks_reto, seleccionar_paso_reto
from utils.formato import formatear_pick

def enviar_mini_reto_free():
    pasos = []

    picks = obtener_picks_reto()
    if not picks or len(picks) < 4:
        enviar_mensaje_free("🚫 No hay suficientes picks para armar el Mini Reto Escalera hoy.")
        return

    for paso in range(1, 5):
        pick = seleccionar_paso_reto(picks, paso)
        if pick:
            formateado = formatear_pick(pick, pick['analisis'], reto_escalera=True, paso=paso)
            pasos.append(f"*Paso {paso}*
{formateado}")

    if pasos:
        enviar_mensaje_free("🌱 *Mini Reto Escalera (4 pasos)* 🌱")
        for paso in pasos:
            enviar_mensaje_free(paso)
    else:
        enviar_mensaje_free("⚠️ No se pudo generar el Mini Reto Escalera esta semana.")
