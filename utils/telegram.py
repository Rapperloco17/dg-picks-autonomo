
# utils/telegram.py

def enviar_mensaje(canal, mensaje):
    print(f"[{canal.upper()}] {mensaje}")

def enviar_mensaje_free(mensaje):
    enviar_mensaje("FREE", mensaje)

def enviar_mensaje_reto(mensaje):
    enviar_mensaje("RETO", mensaje)

def log_envio(msg):
    print(f"[LOG] {msg}")
