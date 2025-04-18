import json
import os
from datetime import datetime
from utils.telegram import log_envio
from utils.soccer_stats import analizar_forma_futbol

OUTPUT_FOLDER = "outputs/"


def cargar_partidos():
    hoy = datetime.now().strftime("%Y-%m-%d")
    archivo = f"futbol_{hoy}.json"
    ruta = os.path.join(OUTPUT_FOLDER, archivo)
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f).get("picks", [])
    return []


def generar_top5():
    partidos = cargar_partidos()
    evaluados = []

    for p in partidos:
        estadisticas = analizar_forma_futbol(p)
        if estadisticas["valor"]:
            evaluados.append({
                "partido": p["partido"],
                "analisis": estadisticas["descripcion"],
                "prom_goles": estadisticas["prom_goles"],
                "btts": estadisticas.get("porcentaje_btts", 0),
                "corners": estadisticas["prom_corners"],
                "tarjetas": estadisticas["prom_tarjetas"]
            })

    # Ordenar por goles + BTTS + valor
    top = sorted(evaluados, key=lambda x: (x["prom_goles"] + x["btts"] / 100), reverse=True)[:5]

    if not top:
        log_envio("free", "⚠️ Hoy no hay partidos con estadísticas destacadas para el Top 5.")
        return

    mensaje = "🔥 *Top 5 Partidos con Valor del Día*\n"
    for i, m in enumerate(top, 1):
        mensaje += f"\n{i}. *{m['partido']}*\n"
        mensaje += f"{m['analisis']}\n"
        mensaje += f"Prom Goles: {m['prom_goles']} | BTTS: {m['btts']}%\n"
        mensaje += f"Corners: {m['corners']} | Tarjetas: {m['tarjetas']}\n"

    log_envio("free", mensaje)


if __name__ == "__main__":
    generar_top5()
