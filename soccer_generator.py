# soccer_generator.py (completo, con BTTS como sección especial)

from utils.api_football import obtener_partidos_de_liga
from utils.soccer_stats import analizar_partido
from utils.formato import formatear_pick
from utils.telegram import enviar_mensaje
from datetime import datetime
from btts_valor import analizar_btts_local_vs_visitante
from utils.historial_picks import guardar_pick_en_historial
import json

# Cargar lista de IDs permitidos desde el JSON
with open("utils/leagues_whitelist_ids.json") as f:
    lista_ids = json.load(f)["allowed_league_ids"]

fecha_hoy = datetime.now().strftime("%Y-%m-%d")
resultados = {}
picks_generados = []
btts_valiosos = []

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

            # Evaluar BTTS con valor
            home = fixture['teams']['home']
            away = fixture['teams']['away']
            stats_home = fixture['teams']['home']
            stats_away = fixture['teams']['away']

            if analizar_btts_local_vs_visitante(stats_home, stats_away):
                texto_btts = f"- {home['name']} vs {away['name']}"
                btts_valiosos.append(texto_btts)
                guardar_pick_en_historial({
                    "partido": f"{home['name']} vs {away['name']}",
                    "pick": "Ambos anotan",
                    "cuota": None,
                    "valor": True,
                    "justificacion": "Promedios ofensivos y defensivos sugieren BTTS con valor.",
                    "categoria": "BTTS"
                })

    except Exception as e:
        print(f"\u26a0\ufe0f Error con liga {liga_id}: {e}")
        resultados[liga_id] = 0

# Enviar picks normales
print("\nResumen de partidos encontrados hoy:")
for liga_id, cantidad in resultados.items():
    print(f"- Liga {liga_id}: {cantidad} partidos")

print("\nPicks generados:")
for pick in picks_generados:
    print(pick)

# Enviar sección especial BTTS
if btts_valiosos:
    mensaje_btts = "\ud83d\udd01 BTTS con Valor\n" + "\n".join(btts_valiosos)
    enviar_mensaje(mensaje_btts, canal="VIP")
    print("\nBTTS con valor detectados:")
    print(mensaje_btts)
