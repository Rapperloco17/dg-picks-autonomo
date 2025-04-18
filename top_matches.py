import json
import os
from datetime import datetime
from utils.telegram import log_envio
from utils.soccer_stats import analizar_forma_futbol

OUTPUT_FOLDER = "outputs"

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
                "prom_goles": estadisticas.get("prom_goles"),
                "btts": estadisticas.get("porcentaje_btts", 0),
                "corners": estadisticas.get("prom_corners"),
                "tarjetas": estadisticas["prom_tarjetas"]
            })

    # Ordenar por goles + BTTS + valor
    top = sorted(evaluados, key=lambda x: (x["prom_goles"] * x["btts"] / 100), reverse=True)[:5]

    if not top:
        log_envio("free", "⚠️ No se encontraron partidos para el Top 5 del día.")
        return

    mensaje = "🔥 *Top 5 Partidos con Más Valor del Día*\n\n"
    for i, p in enumerate(top, 1):
        mensaje += f"*{i}. {p['partido']}*\n"
        mensaje += f"{p['analisis']}\n"
        mensaje += f"Prom. Goles: {p['prom_goles']} | BTTS: {p['btts']}%\n"
        mensaje += f"Corners: {p['corners']} | Tarjetas: {p['tarjetas']}\n\n"

    mensaje += "📊 Basado en análisis estadístico.\n✅ Picks verificados por el sistema DG Picks."
    log_envio("free", mensaje)
