
# utils/mlb_stats.py

def obtener_partidos_mlb():
    return [
        {"equipo1": "Yankees", "equipo2": "Red Sox", "pitcher1": "Cole", "pitcher2": "Sale"},
        {"equipo1": "Dodgers", "equipo2": "Giants", "pitcher1": "Kershaw", "pitcher2": "Webb"}
    ]

def analizar_pitchers(partido):
    return {
        "descripcion": f"{partido['pitcher1']} tiene mejor ERA y más ponches que {partido['pitcher2']}."
    }
