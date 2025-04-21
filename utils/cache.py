# utils/cache.py
import os
import json

CACHE_DIR = "cache_fixtures"

# Crear carpeta si no existe
os.makedirs(CACHE_DIR, exist_ok=True)

def guardar_fixture_cache(fixture_id, data):
    path = os.path.join(CACHE_DIR, f"{fixture_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cargar_fixture_cache(fixture_id):
    path = os.path.join(CACHE_DIR, f"{fixture_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def fixture_en_cache(fixture_id):
    path = os.path.join(CACHE_DIR, f"{fixture_id}.json")
    return os.path.exists(path)
