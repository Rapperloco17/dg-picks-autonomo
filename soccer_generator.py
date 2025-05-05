import os
from utils.partidos_disponibles import obtener_partidos_disponibles
from analysis.analizar_partido import analizar_partido
import json

print("⚙️ Ejecutando soccer_generator.py...")

partidos = obtener_partidos_disponibles()

if not partidos:
    print("🚫 No se encontraron partidos para analizar hoy.")
else:
    print(f"✅ Partidos listos para análisis: {len(partidos)}")
    resultados = []

    for partido in partidos:
        local = partido['teams']['home']['name']
        visitante = partido['teams']['away']['name']
        fecha = partido['fixture']['date']
        print(f"➡️ Analizando: {local} vs {visitante} | Fecha: {fecha}")

        try:
            pick = analizar_partido(partido)
            if pick:
                resultados.append(pick)
                print(f"✅ Pick generado: {pick['pick']} | Cuota: {pick['odds']}")
            else:
                print("⚠️ No se encontró pick con valor en este partido.")
        except Exception as e:
            print(f"❌ Error al analizar {local} vs {visitante}: {e}")

    if resultados:
        os.makedirs("output", exist_ok=True)
        with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        print(f"📁 Picks guardados en output/picks_futbol.json")
    else:
        print("⚠️ No se generaron picks con valor hoy.")
