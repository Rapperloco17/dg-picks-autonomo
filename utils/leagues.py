import json

def cargar_ligas_permitidas():
    with open("utils/leagues_whitelist_ids.json", "r") as f:
        data = json.load(f)
        return data  # Ya es una lista directamente
