import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from openai import OpenAI
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
MIN_PUNTAJE = 0.25
MIN_CUOTA = 1.50
MAX_CUOTA = 3.50
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

async def get_openai_justificacion(pick):
    try:
        prompt = f"Redacta un mini análisis profesional, táctico y convincente para este pick de béisbol MLB, ideal para una combinada tipo Parlay Soñador. Sé claro, breve y convincente:\n\n{pick['msg']}"
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en apuestas deportivas y redactor premium para un canal de picks."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error al generar justificación OpenAI: {e}")
        return "Análisis no disponible."

async def construir_mensaje(picks, cuota_total):
    encabezado = f"\n🍒 *Parlay Soñador del Día – MLB ({FECHA_TEXTO})* 🍒\n\n🔥 Hoy combinamos picks con fundamentos y valor real. Esta es nuestra bomba para hoy:\n"
    cuerpo = ""
    for i, pick in enumerate(picks, 1):
        equipo = extraer_equipo(pick["msg"])
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        linea = pick["msg"].split("\n")[-1]
        justificacion = await get_openai_justificacion(pick)
        cuerpo += f"{i}⃣ – 🍎 Pick: *{equipo}* {linea}\n🧠 {justificacion}\n\n"
    cierre = f"💬 *Cuota total combinada real:* @ {cuota_total}\n\n🎯 Stake bajo. Parlay con selecciones reales, justificación táctica y fundamentos analizados por DG Picks + OpenAI."
    return encabezado + cuerpo + cierre

async def main():
    picks_ml_all = picks_ml()
    picks_rl_all = picks_rl()

    picks_filtrados = []
    enfrentamientos_usados = set()

    todos_los_picks = sorted(picks_ml_all + picks_rl_all, key=lambda x: x.get("puntaje", 0), reverse=True)

    for pick in todos_los_picks:
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        if (
            "cuota" in pick and
            pick["puntaje"] >= MIN_PUNTAJE and
            "⚠️ Sin valor de apuesta" not in pick["msg"] and
            MIN_CUOTA <= float(pick["cuota"]) <= MAX_CUOTA and
            enfrentamiento not in enfrentamientos_usados
        ):
            picks_filtrados.append(pick)
            enfrentamientos_usados.add(enfrentamiento)
        if len(picks_filtrados) >= 6:
            break

    if len(picks_filtrados) < MIN_PICKS:
        logger.info("No hay suficientes picks para formar la Soñadora (min 4)")
        await enviar_mensaje("🚫 Hoy no se pudo construir una Soñadora con valor real.\nSeguimos firmes: solo jugamos cuando hay fundamentos. 🔍", CHAT_ID_FREE)
        return

    cuota_total = calcular_cuota_combinada(picks_filtrados)
    mensaje = await construir_mensaje(picks_filtrados, cuota_total)
    await enviar_mensaje(mensaje, CHAT_ID_FREE)

if __name__ == "__main__":
    asyncio.run(main())
