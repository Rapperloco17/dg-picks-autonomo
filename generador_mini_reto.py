# generador_mini_reto.py

from utils.reto_stats import obtener_picks_reto, seleccionar_paso_reto
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje_free
from utils.cuotas_cache import get_cuota_cached
from utils.cuotas import validar_valor_cuota

def enviar_mini_reto_free():
    pasos = []
    picks = obtener_picks_reto()

    if not picks or len(picks) < 4:
        enviar_mensaje_free("🚫 No hay suficientes picks con valor para el Mini Reto Escalera hoy.")
        return

    for paso in range(1, 5):
        pick = seleccionar_paso_reto(picks, paso)
        if not pick:
            continue

        jugador1 = pick.get("jugador1", "Jugador A")
        jugador2 = pick.get("jugador2", "Jugador B")
        enfrentamiento = f"{jugador1} vs {jugador2}"

        cuota = get_cuota_cached(enfrentamiento, "h2h", "tenis")
        if not validar_valor_cuota(cuota, min_valor=1.50, max_valor=3.50):
            continue

        pick["analisis"]["descripcion"] += f" Cuota: @{cuota}"
        texto = formatear_pick(pick, pick["analisis"], reto_escalera=True, paso=paso)
        pasos.append(texto)

    if pasos:
        enviar_mensaje_free("🌱 *Mini Reto Escalera (4 pasos)* 🌱")
        for paso in pasos:
            enviar_mensaje_free(paso)
    else:
        enviar_mensaje_free("⚠️ No se pudo generar el Mini Reto Escalera esta semana.")
