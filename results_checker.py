import json
import os
from datetime import datetime, timedelta
from utils.telegram import log_envio, enviar_mensaje_privado
from utils.stats_tracker import actualizar_resultados, calcular_estadisticas
from utils.api_football import obtener_resultado_partido
from utils.soccer_utils import interpretar_resultado_pick
from utils.message_templates import obtener_mensaje_resultado

USER_ID_ADMIN = 7450739156
OUTPUT_FOLDER = "outputs/"


def cargar_archivo_picks():
    ayer = datetime.now() - timedelta(days=1)
    nombre_archivo = f"futbol_{ayer.strftime('%Y-%m-%d')}.json"
    ruta = os.path.join(OUTPUT_FOLDER, nombre_archivo)
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f), ruta
    return None, None


def guardar_archivo_picks(data, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def procesar_resultados():
    data, ruta = cargar_archivo_picks()
    if not data:
        print("No se encontró archivo de picks de ayer.")
        return

    total_aciertos = 0
    total_fallos = 0
    unidades_ganadas = 0
    combinadas_acertadas = []

    for pick in data["picks"]:
        if "resultado" in pick:
            continue  # Ya evaluado

        resultado_real = obtener_resultado_partido(pick)
        estado = interpretar_resultado_pick(pick, resultado_real)
        pick["resultado"] = estado

        if estado == "ganado":
            total_aciertos += 1
            unidades_ganadas += float(pick.get("stake", 1)) * (float(pick["cuota"]) - 1)
        else:
            total_fallos += 1
            unidades_ganadas -= float(pick.get("stake", 1))

        # Mensaje verde/rojo por pick
        mensaje = obtener_mensaje_resultado(pick)
        log_envio(pick["canal"], mensaje)

    # Combinadas (Soñadora, Bomba, Conservadora)
    if "combinadas" in data:
        for comb in data["combinadas"]:
            ganadas = all(p["resultado"] == "ganado" for p in comb["picks"])
            if ganadas:
                mensaje_combi = (
                    f"🔥 {comb['nombre']} PEGADA 🔥\n"
                    f"Cuota total @{comb['cuota_total']} reventada con puro valor.\n"
                    f"Análisis real. Estadística pura.\n"
                    f"No fue suerte, fue DG Picks.\n\n"
                    f"📍 Comenta VERDE si la seguiste."
                )
                log_envio("vip", mensaje_combi)
                if "Soñador" in comb["nombre"] or "Bomba" in comb["nombre"]:
                    log_envio("free", mensaje_combi)
                combinadas_acertadas.append(comb["nombre"])

    # Guardar archivo actualizado
    guardar_archivo_picks(data, ruta)

    # Resumen final
    resumen_admin = (
        f"📊 *DG Picks – Resumen de Resultados*\n"
        f"🗓 Fecha: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"✅ Aciertos: {total_aciertos}\n"
        f"❌ Fallos: {total_fallos}\n"
        f"📈 Unidades netas: {round(unidades_ganadas, 2)}\n"
        f"💥 Combinadas acertadas: {', '.join(combinadas_acertadas) if combinadas_acertadas else 'Ninguna'}"
    )
    enviar_mensaje_privado(USER_ID_ADMIN, resumen_admin)
    actualizar_resultados(data["picks"])


if __name__ == "__main__":
    procesar_resultados()
