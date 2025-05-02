import json

def cargar_ligas_permitidas():
    with open("utils/leagues_whitelist_ids.json") as f:
        data = json.load(f)
        return data.get("allowed_league_ids", [])
