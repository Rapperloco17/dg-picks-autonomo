
from utils.telegram import log_envío

mensaje_vip = "🔥 Test final DG Picks VIP\nEste mensaje debería llegar al canal VIP+ correctamente."
mensaje_free = "📢 Test final DG Picks FREE\nEste mensaje debería llegar al nuevo canal FREE correctamente."
mensaje_reto = "⚡ Test final DG Picks RETO\nEste mensaje debería llegar al canal del Reto Escalera correctamente."

log_envío('vip', mensaje_vip)
log_envío('free', mensaje_free)
log_envío('reto', mensaje_reto)
