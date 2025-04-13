from telegram import log_envio
from tenis import obtener_picks_tenis


def enviar_picks_tenis():
    picks = obtener_picks_tenis()

    for pick in picks:
        jugador1 = pick['jugador1']
        jugador2 = pick['jugador2']
        jugador1_rompe = pick['jugador1_rompe']
        jugador2_rompe = pick['jugador2_rompe']
        cuota = pick['cuota']
        descripcion = pick['descripcion']

        rompe1_txt = "rompe" if jugador1_rompe else "NO rompe"
        rompe2_txt = "rompe" if jugador2_rompe else "NO rompe"

        mensaje = f"""
🎾 Pick Tenis – Rompimientos 1er Set

✅ {jugador1} {rompe1_txt} / ❌ {jugador2} {rompe2_txt}

📊 {descripcion}
Cuota estimada: {cuota}

➡️ Revisa cuota real en Bet365.
✅ Valor detectado en el análisis.
"""

        log_envio('vip', mensaje.strip())
        log_envio('free', mensaje.strip())

    print("✅ Picks de tenis con rompimientos enviados correctamente.")
