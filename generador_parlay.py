# generador_parlay.py

from utils.historico_picks import obtener_mejores_picks_del_dia
from utils.telegram import enviar_mensaje
from utils.cuotas import validar_valor_cuota

def enviar_parlay_diario(es_bomba=False):
    picks = obtener_mejores_picks_del_dia()

    if not picks or len(picks) < 2:
        enviar_mensaje("VIP", "🚫 No hay suficientes picks con valor para armar el parlay diario.")
        return

    parlay = []
    cuota_total = 1.0
    todos_validos = True

    for pick in picks:
        cuota = pick.get("cuota", 1.0)

        if not validar_valor_cuota(cuota, min_valor=1.50, max_valor=3.50):
            todos_validos = False
            continue

        parlay.append(pick)
        cuota_total *= cuota

    if len(parlay) < 2:
        enviar_mensaje("VIP", "⚠️ No hay suficientes cuotas válidas para armar un parlay con valor.")
        return

    mensaje = "🎯 *PARLAY DIARIO CON VALOR REAL* 🎯\n\n"
    for i, pick in enumerate(parlay, start=1):
        mensaje += f"{i}. {pick['texto']}\n"

    mensaje += f"\n💰 *Cuota combinada:* @{round(cuota_total, 2)}"
    mensaje += "\nStake sugerido: 2/10"

    if es_bomba and cuota_total >= 150 and todos_validos:
        mensaje = f"💣 *BOMBA LEGENDARIA DEL DÍA* 💣\n\n{mensaje}"

    enviar_mensaje("VIP", mensaje)
