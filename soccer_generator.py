from utils.api_football import obtener_partidos_de_liga
from utils.soccer_stats import analizar_partido
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from datetime import datetime
import json

def log_seguro(mensaje):
    try:
        print(str(mensaje).encode('utf-8', errors='ignore').decode('utf-8'))
    except Exception:
        pass

# Cargar lista de IDs permitidos desde el JSON
with open("utils/leagues_whitelist_ids.json", encoding="utf-8") as f:
    lista_ids = json.load(f)["allowed_league_ids"]

# Fecha actual
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# Resultados por liga
resultados = {}

# Lista final de mensajes generados (picks)
picks_generados = []

for liga_id in lista_ids:
    try:
        data = obtener_partidos_de_liga(int(liga_id), fecha_hoy)
        cantidad = len(data.get("response", []))
        resultados[liga_id] = cantidad

        for fixture in data.get("response", []):
            analisis = analizar_partido(fixture)
            if analisis and analisis.get("valor", False):
                mensaje = formatear_pick(analisis)
                picks_generados.append(mensaje)
                enviar_mensaje(mensaje, canal="VIP")

    except Exception as e:
        log_seguro(f"⚠️ Error analizando partido: {e}")
        resultados[liga_id] = 0

# Imprimir resumen
log_seguro("\nResumen de partidos encontrados hoy:")
for liga_id, cantidad in resultados.items():
    log_seguro(f"- Liga {liga_id}: {cantidad} partidos")

# Imprimir resumen de picks
log_seguro("\nPicks generados:")
for pick in picks_generados:
    log_seguro(pick)
