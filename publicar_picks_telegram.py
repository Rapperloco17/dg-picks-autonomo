import os
import openai
import requests

# Leer variables desde entorno
openai.api_key = os.getenv("OPENAI_API_KEY")
token_telegram = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id_vip = os.getenv("CHAT_ID_VIP")
chat_id_free = os.getenv("CHAT_ID_FREE")

picks_generados = [
    {
        "partido": "Cincinnati Reds vs Pittsburgh Pirates",
        "pick": "Under 8.0",
        "cuota": 1.93,
        "estimado": 5.7,
        "linea": 8.0,
        "tipo": "candado"
    },
    {
        "partido": "Phillies vs Rockies",
        "pick": "Over 8.5",
        "cuota": 1.90,
        "estimado": 11.2,
        "linea": 8.5,
        "tipo": "normal"
    }
]

def generar_mensaje_ia(partido, pick, cuota, linea, estimado):
    prompt = f"""
    Genera un mensaje de análisis profesional de apuestas deportivas estilo DG Picks para Telegram con este contexto:
    Partido: {partido}
    Línea: {linea} carreras
    Estimado DG Picks: {estimado} carreras
    Pick: {pick} @ {cuota}
    No menciones IA ni OpenAI. Usa lenguaje directo, confiable, con iconos si aplica y termina con ✅ Valor detectado en la cuota.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un analista experto de apuestas deportivas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"{partido}\n{pick} @ {cuota} | Línea: {linea} | Estimado: {estimado}\n✅ Valor detectado en la cuota"

def enviar_a_telegram(token, chat_id, mensaje):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}
    return requests.post(url, data=data)

for pick in picks_generados:
    partido = pick["partido"]
    pick_txt = pick["pick"]
    cuota = pick["cuota"]
    linea = pick["linea"]
    estimado = pick["estimado"]
    tipo = pick["tipo"]

    mensaje = generar_mensaje_ia(partido, pick_txt, cuota, linea, estimado)
    destino = chat_id_vip if tipo == "candado" else chat_id_free

    resp = enviar_a_telegram(token_telegram, destino, mensaje)
    print(f"Enviado ({tipo.upper()}) -> {partido} | Status: {resp.status_code}")
