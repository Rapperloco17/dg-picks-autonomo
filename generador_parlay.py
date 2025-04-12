
# generador_parlay.py

from utils.telegram import enviar_mensaje
from utils.historico_picks import obtener_mejores_picks_del_dia
from utils.formato import formatear_parlay

def enviar_parlay_diario(es_bomba=False):
    picks = obtener_mejores_picks_del_dia()

    if not picks or len(picks) < 2:
        enviar_mensaje("vip", "🚫 No hay suficientes picks con valor para armar el parlay diario.")
        return

    if es_bomba:
        parlay = formatear_parlay(picks, cuota_minima=50.0)
        if parlay:
            enviar_mensaje("vip", "💣 *BOMBA LEGENDARIA DEL FIN DE SEMANA* 💣")
            enviar_mensaje("vip", parlay)
        else:
            enviar_mensaje("vip", "⚠️ No se pudo armar la bomba legendaria hoy.")
    else:
        parlay = formatear_parlay(picks, cuota_minima=2.0)
        if parlay:
            enviar_mensaje("vip", "🎯 *Parlay Diario DG Picks* 🎯")
            enviar_mensaje("vip", parlay)
        else:
            enviar_mensaje("vip", "⚠️ No se pudo armar el parlay diario hoy.")
