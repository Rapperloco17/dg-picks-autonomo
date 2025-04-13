
from utils.telegram import log_envío

mensaje = (
    "🥋 *PICK UFC – MODO BESTIA ACTIVADO*

"
    "*Volkanovski vs López*
"
    "💣 _Volkanovski gana por KO/TKO_

"
    "📊 *Análisis:* El campeón viene con hambre. Superioridad total en striking, agresividad y volumen. "
    "López no tiene con qué sostener el castigo por 5 rounds. Si Volka conecta limpio, esto se acaba.

"
    "🔥 *Cuota con valor* + *Lectura de pelea clara*
"
    "💥 *Stake:* 2/10

"
    "✅ _¡Valor detectado!_
"
    "🔒 Este pick es digno de confianza… ¿vas con nosotros o lo ves desde la banca?"
)

# Enviar a los tres canales
log_envío('vip', mensaje)
log_envío('free', mensaje)
log_envío('reto', mensaje)
