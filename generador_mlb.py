from utils.sofascore import obtener_partidos_mlb
from utils.telegram import log_envio
from utils.valor_cuota import detectar_valor_mlb
from utils.mlb_stats import analizar_mlb

def enviar_picks_mlb():
    print("📊 Iniciando análisis de MLB...")
    partidos = obtener_partidos_mlb()

    for partido in partidos:
        if detectar_valor_mlb(partido["cuota"]):
            análisis = analizar_mlb(partido)
            mensaje = f"📌 *Pick de MLB*\n\n{análisis}"
            log_envio(mensaje)

    print("✅ Picks de MLB enviados.")
