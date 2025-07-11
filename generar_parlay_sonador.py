import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from dg_picks_mlb import sugerir_picks as picks_ml
from dg_picks_mlb_2 import sugerir_picks as picks_rl
import pytz
import openai

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Parlay Soñador")

MX_TZ = pytz.timezone("America/Mexico_City")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B de %Y")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

MIN_PUNTAJE = 0.25
MIN_CUOTA = 1.50
MAX_CUOTA = 3.50
MIN_PICKS = 3
MAX_PICKS = 5

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

def contiene_sin_valor(msg):
    return "⚠️ Sin valor" in msg

def generar_prompt_analisis(equipo, enfrentamiento):
    return f"Da una justificación de apuesta para que el equipo {equipo} gane el partido de béisbol de hoy en el enfrentamiento {enfrentamiento}. Sé breve, confiado y menciona alguna razón táctica o estadística."

def generar_mini_analisis(equipo, enfrentamiento):
    prompt = generar_prompt_analisis(equipo, enfrentamiento)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=60,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error con OpenAI: {e}")
        return "Pick respaldado por fundamentos sólidos."

def construir_mensaje(picks, cuota_total):
    encabezado = f"🎯 *Parlay Soñador del Día – MLB 🔥 {FECHA_TEXTO}* 🎯\n\n💥 Hoy combinamos selecciones con *valor real* y respaldo estadístico para formar nuestra bomba soñadora. Aquí va:\n\n"
    cuerpo = ""
    for i, pick in enumerate(picks, 1):
        equipo = extraer_equipo(pick["msg"])
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        linea = [l for l in pick["msg"].split("\n") if "@" in l][-1]
        mini = generar_mini_analisis(equipo, enfrentamiento)
        cuerpo += f"*{i}️⃣ {equipo}* {linea} (Puntaje: {pick['puntaje']:.2f})\n🧠 _{mini}_\n\n"
    cierre = f"💣 *Cuota total combinada:* @ {cuota_total}\n📊 Stake bajo – combinada de picks reales, bien analizados.\n\n🔥 *Esto no es humo, es análisis. DG Picks siempre apuesta con cabeza, no con corazón.*\n💼📈 *¡Vamos por el verde, soñadores!*"
    return encabezado + cuerpo + cierre

async def main():
    picks_ml_all = picks_ml()
    picks_rl_all = picks_rl()

    picks_filtrados = []
    enfrentamientos_usados = set()

    todos = sorted(picks_ml_all + picks_rl_all, key=lambda x: x["puntaje"], reverse=True)

    for pick in todos:
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        if (
            pick["puntaje"] >= MIN_PUNTAJE and
            MIN_CUOTA <= float(pick["cuota"]) <= MAX_CUOTA and
            enfrentamiento not in enfrentamientos_usados and
            not contiene_sin_valor(pick["msg"])
        ):
            picks_filtrados.append(pick)
            enfrentamientos_usados.add(enfrentamiento)
        if len(picks_filtrados) >= MAX_PICKS:
            break

    if len(picks_filtrados) < MIN_PICKS:
        await enviar_mensaje("🚫 Hoy no se pudo construir una Soñadora con valor real.\nSeguimos firmes: solo jugamos cuando hay fundamentos. 🔍", CHAT_ID_FREE)
        return

    cuota_total = calcular_cuota_combinada(picks_filtrados)
    mensaje = construir_mensaje(picks_filtrados, cuota_total)
    await enviar_mensaje(mensaje, CHAT_ID_FREE)

if __name__ == "__main__":
    asyncio.run(main())

