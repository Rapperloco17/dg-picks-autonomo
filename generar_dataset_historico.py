import os
import json
import pandas as pd
from collections import defaultdict

CARPETA_HISTORIAL = "historial"
SALIDA_JSON = "output/team_stats_global.json"
SALIDA_EXCEL = "output/team_stats_global.xlsx"
os.makedirs("output", exist_ok=True)

# 1. Combinar todos los archivos JSON
partidos_totales = []
for archivo in os.listdir(CARPETA_HISTORIAL):
    if archivo.startswith("resultados_") and archivo.endswith(".json"):
        with open(os.path.join(CARPETA_HISTORIAL, archivo), encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    partidos_totales.extend(data)
                    print(f"✅ Cargado: {archivo} ({len(data)} partidos)")
            except Exception as e:
                print(f"❌ Error cargando {archivo}: {e}")

# 2. Calcular estadísticas por equipo
equipos = defaultdict(lambda: {
    "PJ": 0, "GF": 0, "GC": 0, "BTTS": 0, "Over_2.5": 0,
    "Victorias": 0, "Empates": 0, "Derrotas": 0, "Forma": []
})

for partido in partidos_totales:
    try:
        loc = partido["equipo_local"]
        vis = partido["equipo_visitante"]
        gl = int(partido["goles_local"])
        gv = int(partido["goles_visitante"])

        for equipo, gf, gc in [(loc, gl, gv), (vis, gv, gl)]:
            equipos[equipo]["PJ"] += 1
            equipos[equipo]["GF"] += gf
            equipos[equipo]["GC"] += gc
            if gf > 0 and gc > 0:
                equipos[equipo]["BTTS"] += 1
            if gf + gc >= 3:
                equipos[equipo]["Over_2.5"] += 1

        if gl > gv:
            equipos[loc]["Victorias"] += 1
            equipos[vis]["Derrotas"] += 1
            equipos[loc]["Forma"].append("W")
            equipos[vis]["Forma"].append("L")
        elif gv > gl:
            equipos[vis]["Victorias"] += 1
            equipos[loc]["Derrotas"] += 1
            equipos[vis]["Forma"].append("W")
            equipos[loc]["Forma"].append("L")
        else:
            equipos[loc]["Empates"] += 1
            equipos[vis]["Empates"] += 1
            equipos[loc]["Forma"].append("D")
            equipos[vis]["Forma"].append("D")

    except Exception as e:
        print(f"⚠️ Partido con error: {e}")

# 3. Guardar como JSON y Excel
resumen = []
for nombre, stats in equipos.items():
    pj = stats["PJ"] or 1  # evitar división por cero
    resumen.append({
        "Equipo": nombre,
        "PJ": stats["PJ"],
        "GF": round(stats["GF"] / pj, 2),
        "GC": round(stats["GC"] / pj, 2),
        "%BTTS": round(stats["BTTS"] / pj * 100, 1),
        "%Over2.5": round(stats["Over_2.5"] / pj * 100, 1),
        "W": stats["Victorias"],
        "D": stats["Empates"],
        "L": stats["Derrotas"],
        "Forma": ''.join(stats["Forma"][-5:])
    })

# Guardar archivos
with open(SALIDA_JSON, "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)

pd.DataFrame(resumen).to_excel(SALIDA_EXCEL, index=False)

print(f"✅ Historial generado: {SALIDA_JSON} y {SALIDA_EXCEL}")
