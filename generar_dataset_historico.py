import os
import json
import pandas as pd

JSON_DIR = "historial"
OUTPUT_JSON = "output/team_stats_global.json"


def calcular_estadisticas(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    partidos = pd.DataFrame(data)

    equipos = {}
    for _, row in partidos.iterrows():
        local = row["equipo_local"]
        visitante = row["equipo_visitante"]

        if local not in equipos:
            equipos[local] = {
                "partidos": 0, "goles_favor": 0, "goles_contra": 0, "victorias": 0,
                "empates": 0, "derrotas": 0, "btts": 0, "over_2_5": 0
            }
        if visitante not in equipos:
            equipos[visitante] = {
                "partidos": 0, "goles_favor": 0, "goles_contra": 0, "victorias": 0,
                "empates": 0, "derrotas": 0, "btts": 0, "over_2_5": 0
            }

        # Resultado
        gf_local = row["goles_local"]
        gf_visitante = row["goles_visitante"]

        equipos[local]["partidos"] += 1
        equipos[visitante]["partidos"] += 1
        equipos[local]["goles_favor"] += gf_local
        equipos[local]["goles_contra"] += gf_visitante
        equipos[visitante]["goles_favor"] += gf_visitante
        equipos[visitante]["goles_contra"] += gf_local

        if gf_local > gf_visitante:
            equipos[local]["victorias"] += 1
            equipos[visitante]["derrotas"] += 1
        elif gf_local < gf_visitante:
            equipos[visitante]["victorias"] += 1
            equipos[local]["derrotas"] += 1
        else:
            equipos[local]["empates"] += 1
            equipos[visitante]["empates"] += 1

        if gf_local > 0 and gf_visitante > 0:
            equipos[local]["btts"] += 1
            equipos[visitante]["btts"] += 1

        if (gf_local + gf_visitante) > 2:
            equipos[local]["over_2_5"] += 1
            equipos[visitante]["over_2_5"] += 1

    return equipos


if __name__ == "__main__":
    print("📊 Generando dataset global desde JSON...")

    todos_equipos = {}
    for archivo in os.listdir(JSON_DIR):
        if archivo.endswith(".json") and archivo.startswith("resultados_"):
            ruta = os.path.join(JSON_DIR, archivo)
            print(f"✅ Procesando {archivo}...")
            equipos = calcular_estadisticas(ruta)
            for nombre, datos in equipos.items():
                if nombre not in todos_equipos:
                    todos_equipos[nombre] = datos
                else:
                    for key in datos:
                        todos_equipos[nombre][key] += datos[key]

    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(todos_equipos, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo guardado: {OUTPUT_JSON}")
