import os
import json
from collections import defaultdict
import re

CARPETA_ENTRADA = "descargas"
CARPETA_SALIDA = "unificados"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

# Agrupar archivos por nombre de liga
ligas = defaultdict(list)

for archivo in os.listdir(CARPETA_ENTRADA):
    if archivo.startswith("resultados_") and archivo.endswith(".json"):
        nombre_sin_ext = archivo.replace("resultados_", "").replace(".json", "")
        match = re.match(r"(.*)_\d{4}$", nombre_sin_ext)
        if match:
            nombre_liga = match.group(1)
            ligas[nombre_liga].append(archivo)

# Combinar por liga
for liga, archivos in ligas.items():
    partidos = []
    for archivo in archivos:
        ruta = os.path.join(CARPETA_ENTRADA, archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    partidos.extend(data)
        except Exception as e:
            print(f"❌ Error leyendo {archivo}: {e}")

    if partidos:
        salida = os.path.join(CARPETA_SALIDA, f"resultados_{liga}.json")
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(partidos, f, ensure_ascii=False, indent=2)
        print(f"✅ Liga combinada: {liga} ({len(partidos)} partidos)")
    else:
        print(f"⚠️ Liga vacía: {liga}")

