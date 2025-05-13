import os
import json
import pandas as pd
from collections import defaultdict

# Carpeta donde están los archivos de resultados
HISTORIAL_DIR = "historial"

# Estructura base por equipo
team_stats = defaultdict(lambda: {
    "partidos": 0,
    "goles_a_favor": 0,
    "goles_en_contra": 0,
    "victorias": 0,
    "empates": 0,
    "derrotas": 0,
    "btts": 0,
    "over_2_5": 0,
    "forma": []  # W, D, L
})

# Leer todos los archivos .json en /historial
for filename in os.listdir(HISTORIAL_DIR):
    if filename.endswith(".json") and filename.startswith("resultados_"):
        path = os.path.join(HISTORIAL_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            partidos = json.load(f)

        for partido in partidos:
            local = partido["local"]
            visitante = partido["visitante"]
            gl = partido["goles_local"]
            gv = partido["goles_visitante"]

            # Local
            team_stats[local]["partidos"] += 1
            team_stats[local]["goles_a_favor"] += gl
            team_stats[local]["goles_en_contra"] += gv
            team_stats[local]["btts"] += int(gl > 0 and gv > 0)
            team_stats[local]["over_2_5"] += int(gl + gv > 2.5)
            if gl > gv:
                team_stats[local]["victorias"] += 1
                team_stats[local]["forma"].append("W")
            elif gl == gv:
                team_stats[local]["empates"] += 1
                team_stats[local]["forma"].append("D")
            else:
                team_stats[local]["derrotas"] += 1
                team_stats[local]["forma"].append("L")

            # Visitante
            team_stats[visitante]["partidos"] += 1
            team_stats[visitante]["goles_a_favor"] += gv
            team_stats[visitante]["goles_en_contra"] += gl
            team_stats[visitante]["btts"] += int(gl > 0 and gv > 0)
            team_stats[visitante]["over_2_5"] += int(gl + gv > 2.5)
            if gv > gl:
                team_stats[visitante]["victorias"] += 1
                team_stats[visitante]["forma"].append("W")
            elif gl == gv:
                team_stats[visitante]["empates"] += 1
                team_stats[visitante]["forma"].append("D")
            else:
                team_stats[visitante]["derrotas"] += 1
                team_stats[visitante]["forma"].append("L")

# Convertir a resumen por equipo
resumen = []
for equipo, datos in team_stats.items():
    pj = datos["partidos"]
    if pj == 0:
        continue
    resumen.append({
        "Equipo": equipo,
        "Partidos": pj,
        "Goles a Favor": round(datos["goles_a_favor"] / pj, 2),
        "Goles en Contra": round(datos["goles_en_contra"] / pj, 2),
        "% BTTS": round(datos["btts"] / pj * 100, 1),
        "% Over 2.5": round(datos["over_2_5"] / pj * 100, 1),
        "% Victorias": round(datos["victorias"] / pj * 100, 1),
        "% Empates": round(datos["empates"] / pj * 100, 1),
        "% Derrotas": round(datos["derrotas"] / pj * 100, 1),
        "Últimos 5": "-".join(datos["forma"][-5:])
    })

# Guardar resultados
os.makedirs("output", exist_ok=True)

# Guardar como JSON (para el sistema)
with open("output/team_stats_global.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)

# 🚫 Comentado para evitar error en Railway
# pd.DataFrame(resumen).to_excel("output/team_stats_global.xlsx", index=False)

print("✅ Análisis por equipo generado correctamente.")
