import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from dg_picks_mlb import sugerir_picks as picks_ml
from dg_picks_mlb_2 import sugerir_picks as picks_rl

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Parlay Soñador")

MX_TZ = datetime.now().astimezone().tzinfo
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")

# Parámetros
MIN_PUNTAJE = 0.30
MIN_CUOTA = 1.50
MAX_CUOTA = 3.50
CUOTA_OBJETIVO = 10.0
MIN_PICKS = 4

async def enviar_mensaje(mensaje: str, chat_id: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error al enviar mensaje: {e}")

def extraer_equipo(msg):
    for linea in msg.split("\n"):
        if "Pick:" in linea:
            partes = linea.split("Pick:")[1].strip().split(" ")
            return partes[0] if partes else ""
    return ""

def extraer_enfrentamiento(msg):
    for linea in msg.split("\n"):
        if "vs" in linea:
            return linea.strip()
    return ""

def calcular_cuota_combinada(picks):
    total = 1.0
    for p in picks:
        try:
            linea = [l for l in p["msg"].split("\n") if "@" in l][-1]
            cuota_str = linea.split("@")[-1].split(" ")[0].strip()
            total *= float(cuota_str)
        except:
            pass
    return round(total, 2)

def construir_mensaje(picks, cuota_total):
    encabezado = f"\n🎯 *Parlay Soñador del Día – MLB* 🎯\n\n🔥 Hoy combinamos valor con fundamentos. Aquí va nuestra bomba:\n"
    cuerpo = ""
    for i, pick in enumerate(picks, 1):
        equipo = extraer_equipo(pick["msg"])
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        linea = pick["msg"].split("\n")[-1]
        cuerpo += f"{i}⃣ *{equipo}* – {linea}\n\_{enfrentamiento}_\n\n"
    cierre = f"💣 *Cuota total combinada:* @ {cuota_total}\n\nStake bajo. Pick con selecciones reales y fundamentos.\n"
    return encabezado + cuerpo + cierre

async def main():
    picks_ml_all = picks_ml()
    picks_rl_all = picks_rl()

    picks_filtrados = []
    enfrentamientos_usados = set()

    for pick in sorted(picks_ml_all + picks_rl_all, key=lambda x: x["puntaje"], reverse=True):
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        if (pick["puntaje"] >= MIN_PUNTAJE and
            MIN_CUOTA <= float(pick["cuota"]) <= MAX_CUOTA and
            enfrentamiento not in enfrentamientos_usados):
            picks_filtrados.append(pick)
            enfrentamientos_usados.add(enfrentamiento)
        if len(picks_filtrados) >= 6:
            break

    if len(picks_filtrados) < MIN_PICKS:
        logger.info("No hay suficientes picks para formar la Soñadora (min 4)")
        await enviar_mensaje("🚫 Hoy no se pudo construir una Soñadora con valor real.\nSeguimos firmes: solo jugamos cuando hay fundamentos. 🔍", CHAT_ID_FREE)
        return

    cuota_total = calcular_cuota_combinada(picks_filtrados)
    if cuota_total < CUOTA_OBJETIVO:
        logger.info("No se alcanzó la cuota mínima para Soñadora")
        await enviar_mensaje("🚫 Hoy no se pudo construir una Soñadora con cuota suficiente.\nSeguimos firmes: solo jugamos cuando hay fundamentos. 🔍", CHAT_ID_FREE)
        return

    mensaje = construir_mensaje(picks_filtrados, cuota_total)
    await enviar_mensaje(mensaje, CHAT_ID_FREE)

if __name__ == "__main__":
    asyncio.run(main())
