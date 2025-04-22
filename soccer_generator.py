from utils.api_football import obtener_partidos_de_liga
from utils.soccer_stats import analizar_partido
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from datetime import datetime
import json

# Cargar lista de IDs permitidos desde el JSON
with open("utils/leagues_whitelist_ids.json") as f:
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
        print(f"⚠️ Error con liga {liga_id}:".encode('utf-8', 'ignore').decode('utf-8'), str(e))

# Imprimir resumen
print("\nResumen de partidos encontrados hoy:".encode('utf-8', 'ignore').decode('utf-8'))
for liga_id, cantidad in resultados.items():
    print(f"- Liga {liga_id}: {cantidad} partidos".encode('utf-8', 'ignore').decode('utf-8'))

# Imprimir picks generados
print("\nPicks generados:".encode('utf-8', 'ignore').decode('utf-8'))
for pick in picks_generados:
    print(pick.encode('utf-8', 'ignore').decode('utf-8'))
