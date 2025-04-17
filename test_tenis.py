# ✅ Test manual de generación y envío de picks de tenis reales desde Sofascore

from utils.sofascore import obtener_picks_tenis
from utils.telegram import log_envio, enviar_mensaje_privado

def test_tenis():
    picks = obtener_picks_tenis()
    total = len(picks)

    # Mensaje resumen para administrador
    resumen = f"📊 Test Picks Tenis\n"
    resumen += f"🎾 Picks generados: {total}\n"

    if total == 0:
        resumen += "❌ No se encontraron picks para hoy.\n"
    else:
        resumen += "✅ Se generaron picks correctamente.\n"

    enviar_mensaje_privado(7450739156, resumen)

    for pick in picks:
        if "canal" not in pick:
            print("❌ No se especificó canal para el pick:", pick)
            continue

        mensaje = (
            f"🎾 Pick Tenis\n"
            f"📅 Partido: {pick['partido']}\n"
            f"🧠 Análisis: {pick['analisis']}\n"
            f"💸 Cuota: {pick['cuota']}\n"
            f"⚖️ Stake: {pick['stake']}\n"
            f"✅ Valor detectado en la cuota."
        )

        log_envio(pick["canal"], mensaje)

if __name__ == "__main__":
    test_tenis()

