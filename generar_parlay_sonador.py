import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from dg_picks_mlb import sugerir_picks as picks_ml
from dg_picks_mlb_2 import sugerir_picks as picks_rl
import pytz
from openai import OpenAI

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Parlay Soñador")

MX_TZ = pytz.timezone("America/Mexico_City")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B de %Y")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CUOTA_OBJETIVOS = [10, 20, 30, 100]
MIN_PUNTAJE = 0.25
MIN_CUOTA = 1.50
MIN_PICKS = 4
MAX_PICKS = 8

async def enviar_mensaje(mensaje: str, chat_id: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode="Markdown")
        logger.info(f"Mensaje enviado a Telegram (chat_id: {chat_id})")
    except Exception as e:
        logger.error(f"Error al enviar mensaje: {e}")

def extraer_equipo(msg: str) -> str:
    for linea in msg.split("\n"):
        if "Pick:" in linea:
            partes = linea.split("Pick:")[1].strip().split(" ")
            return partes[0] if partes else "Desconocido"
    return "Desconocido"

def extraer_enfrentamiento(msg: str) -> str:
    for linea in msg.split("\n"):
        if "vs" in linea:
            return linea.strip()
    return "Enfrentamiento desconocido"

def calcular_cuota_combinada(picks: list) -> float:
    total = 1.0
    for p in picks:
        try:
            linea = [l for l in p["msg"].split("\n") if "@" in l][-1]
            cuota_str = linea.split("@")[-1].split(" ")[0].strip()
            total *= float(cuota_str)
        except (IndexError, ValueError) as e:
            logger.warning(f"Error al extraer cuota de {p['msg']}: {e}")
            continue
    return round(total, 2)

def contiene_sin_valor(msg: str) -> bool:
    return "⚠️ Sin valor" in msg

def generar_prompt_analisis(equipo: str, enfrentamiento: str) -> str:
    return f"Da una justificación breve y confiada para apostar por {equipo} en el partido de béisbol de hoy ({enfrentamiento}). Incluye una razón táctica o estadística clave."

def generar_mini_analisis(equipo: str, enfrentamiento: str) -> str:
    if not OPENAI_API_KEY:
        return "Pick respaldado por fundamentos sólidos."
    prompt = generar_prompt_analisis(equipo, enfrentamiento)
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error con OpenAI: {e}")
        return "Pick respaldado por fundamentos sólidos."

def construir_mensaje(picks: list, cuota_total: float, objetivo: float) -> str:
    encabezado = f"🎯 *Parlay Soñador del Día – MLB 🔥 {FECHA_TEXTO}* 🎯\n\n💥 Soñadora apuntando a cuota ~{objetivo}. Selecciones con *valor real* y respaldo estadístico. Aquí va:\n\n"
    cuerpo = ""
    for i, pick in enumerate(picks, 1):
        equipo = extraer_equipo(pick["msg"])
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        linea = [l for l in pick["msg"].split("\n") if "@" in l][-1] if any("@" in l for l in pick["msg"].split("\n")) else "Pick sin cuota"
        mini = generar_mini_analisis(equipo, enfrentamiento)
        cuerpo += f"*{i}️⃣ {equipo}* {linea} (Puntaje: {pick['puntaje']:.2f})\n🧠 _{mini}_\n\n"
    cierre = f"💣 *Cuota total combinada:* @ {cuota_total}\n📊 Stake bajo – combinada de picks reales, bien analizados.\n\n🔥 *Esto no es humo, es análisis. DG Picks siempre apuesta con cabeza.*\n💼📈 *¡Vamos por el verde, soñadores!*"
    return encabezado + cuerpo + cierre

async def generar_parlays():
    picks_ml_all = picks_ml()
    picks_rl_all = picks_rl()

    if not picks_ml_all and not picks_rl_all:
        logger.info("No se encontraron picks ML ni RL")
        await enviar_mensaje("🚫 Hoy no se pudo construir una Soñadora con valor real.\nSeguimos firmes: solo jugamos cuando hay fundamentos. 🔍", CHAT_ID_FREE)
        return

    todos = sorted(picks_ml_all + picks_rl_all, key=lambda x: x["puntaje"], reverse=True)
    picks_filtrados = []
    enfrentamientos_usados = set()

    for pick in todos:
        if not isinstance(pick, dict) or "msg" not in pick or "puntaje" not in pick or "cuota" not in pick:
            logger.warning(f"Pick inválido: {pick}")
            continue
        enfrentamiento = extraer_enfrentamiento(pick["msg"])
        try:
            cuota = float(pick["cuota"])
        except (ValueError, TypeError):
            logger.warning(f"Cuota inválida en pick: {pick['msg']}")
            continue
        if (
            pick["puntaje"] >= MIN_PUNTAJE and
            cuota >= MIN_CUOTA and
            enfrentamiento not in enfrentamientos_usados and
            not contiene_sin_valor(pick["msg"])
        ):
            picks_filtrados.append(pick)
            enfrentamientos_usados.add(enfrentamiento)
        if len(picks_filtrados) >= MAX_PICKS * len(CUOTA_OBJETIVOS):  # Suficientes para todos los parlays
            break

    if len(picks_filtrados) < MIN_PICKS:
        logger.info(f"No hay suficientes picks válidos ({len(picks_filtrados)} < {MIN_PICKS})")
        await enviar_mensaje("🚫 Hoy no se pudo construir una Soñadora con valor real.\nSeguimos firmes: solo jugamos cuando hay fundamentos. 🔍", CHAT_ID_FREE)
        return

    for objetivo in CUOTA_OBJETIVOS:
        parlays = []
        cuota_actual = 1.0
        enfrentamientos_usados_parlay = set()

        for pick in picks_filtrados:
            enfrentamiento = extraer_enfrentamiento(pick["msg"])
            if enfrentamiento not in enfrentamientos_usados_parlay and len(parlays) < MAX_PICKS:
                cuota_nueva = calcular_cuota_combinada([pick] + parlays)
                if cuota_nueva >= objetivo and len(parlays) >= MIN_PICKS - 1:  # Asegurar mínimo 3
                    parlays.append(pick)
                    break
                elif cuota_nueva < objetivo and len(parlays) < MAX_PICKS - 1:
                    parlays.append(pick)
                    enfrentamientos_usados_parlay.add(enfrentamiento)
                    cuota_actual = cuota_nueva

        if len(parlays) >= MIN_PICKS:
            cuota_total = calcular_cuota_combinada(parlays)
            mensaje = construir_mensaje(parlays, cuota_total, objetivo)
            await enviar_mensaje(mensaje, CHAT_ID_FREE)
        else:
            logger.info(f"No se pudo alcanzar cuota {objetivo} con {MIN_PICKS} picks")

async def main():
    logger.info(f"Iniciando Parlay Soñador para {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST")
    await generar_parlays()

if __name__ == "__main__":
    if not all([os.getenv("TELEGRAM_BOT_TOKEN"), CHAT_ID_FREE, OPENAI_API_KEY]):
        logger.error("Faltan variables de entorno: TELEGRAM_BOT_TOKEN, CHAT_ID_FREE o OPENAI_API_KEY")
    else:
        asyncio.run(main())
