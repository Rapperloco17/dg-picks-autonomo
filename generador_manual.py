
# generador_manual.py

from utils.telegram import enviar_mensaje, enviar_mensaje_free, enviar_mensaje_reto

def enviar_pick_manual(pick, destino="vip"):
    """
    Envía un pick manualmente al canal deseado.
    :param pick: str, el contenido del pick ya formateado.
    :param destino: str, puede ser 'vip', 'free' o 'reto'
    """
    if destino == "vip":
        enviar_mensaje("vip", "✍️ *Pick Manual Personalizado* ✍️")
        enviar_mensaje("vip", pick)
    elif destino == "free":
        enviar_mensaje_free("✍️ *Pick Manual Personalizado* ✍️")
        enviar_mensaje_free(pick)
    elif destino == "reto":
        enviar_mensaje_reto("✍️ *Pick Manual Personalizado para Reto* ✍️")
        enviar_mensaje_reto(pick)
    else:
        print("❌ Canal de destino no válido. Usa 'vip', 'free' o 'reto'.")
