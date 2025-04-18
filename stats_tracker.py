import os
import json
from datetime import datetime, timedelta
from utils.telegram import enviar_mensaje_privado

HISTORIAL_PATH = "outputs/"
ESTADISTICAS_PATH = "outputs/rendimiento_semanal.json"
USER_ID_ADMIN = 7450739156

def cargar_todos_los_picks():
    picks = []
    for archivo in os.listdir(HISTORIAL_PATH):
        if archivo.startswith("futbol_") and archivo.endswith(".json"):
            with open(os.path.join(HISTORIAL_PATH, archivo), "r", encoding="utf-8") as f:
                data = json.load(f)
                picks.extend(data.get("picks", []))
    return picks

def filtrar_ultima_semana(picks):
    hoy = datetime.now()
    hace_7_dias = hoy - timedelta(days=7)
    return [p for p in picks if "fecha" in p and datetime.strptime(p["fecha"], "%Y-%m-%d") >= hace_7_dias]

def calcular_estadisticas(picks):
    total = len(picks)
    ganados = sum(1 for p in picks if p.get("resultado") == "ganado")
    perdidos = sum(1 for p in picks if p.get("resultado") == "perdido")
    unidades = 0.0

    for p in picks:
        stake = float(p.get("stake", 1))
        cuota = float(p.get("cuota", 1))
        if p.get("resultado") == "ganado":
            unidades += stake * (cuota - 1)
        elif p.get("resultado") == "perdido":
            unidades -= stake

    roi = (unidades / (ganados + perdidos)) * 100 if (ganados + perdidos) > 0 else 0
    return {
        "total_picks": total,
        "ganados": ganados,
        "perdidos": perdidos,
        "porcentaje_acierto": round((ganados / total) * 100, 2) if total > 0 else 0,
        "unidades_netas": round(unidades, 2),
        "roi": round(roi, 2)
    }

def guardar_estadisticas(resumen):
    with open(ESTADISTICAS_PATH, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

def actualizar_resultados(picks):
    resumen = calcular_estadisticas(picks)
    guardar_estadisticas(resumen)

def generar_resumen_semanal():
    picks = cargar_todos_los_picks()
    picks_semana = filtrar_ultima_semana(picks)
    resumen = calcular_estadisticas(picks_semana)
    guardar_estadisticas(resumen)
    return resumen

def enviar_resumen_telegram():
    resumen = generar_resumen_semanal()
    mensaje = (
        f"\ud83d\udcca *Resumen Semanal DG Picks*\n\n"
        f"\ud83d\uddd3\ufe0f Picks: {resumen['total_picks']}\n"
        f"\u2705 Ganados: {resumen['ganados']}\n"
        f"\u274c Perdidos: {resumen['perdidos']}\n"
        f"\ud83c\udfaf Acierto: {resumen['porcentaje_acierto']}%\n"
        f"\ud83d\udcb0 ROI: {resumen['roi']}%\n"
        f"\ud83d\udcc8 Unidades netas: {resumen['unidades_netas']}"
    )
    enviar_mensaje_privado(USER_ID_ADMIN, mensaje)

if __name__ == "__main__":
    enviar_resumen_telegram()
