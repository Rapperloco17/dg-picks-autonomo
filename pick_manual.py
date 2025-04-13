from utils.telegram import log_envío

def enviar_pick_manual():
    mensaje = "📢 PICK MANUAL DG PICKS 💣\n\n🧠 Volkanovski gana por KO/TKO a López (UFC)\n🔥 Stake: 2/10\n\n📢 ¡Solo para valientes, esto se va a cobrar!"
    
    log_envío('vip', mensaje)
