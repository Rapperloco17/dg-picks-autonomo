# utils/valor_cuota.py

def detectar_valor_tenis(cuota):
    try:
        cuota = float(cuota)
        return 1.70 <= cuota <= 3.50
    except:
        return False

def detectar_valor_mlb(cuota):
    try:
        cuota = float(cuota)
        return 1.60 <= cuota <= 3.50
    except:
        return False

def detectar_valor_nba(cuota):
    try:
        cuota = float(cuota)
        return 1.60 <= cuota <= 3.50
    except:
        return False

def detectar_valor_futbol(cuota):
    try:
        cuota = float(cuota)
        return 1.50 <= cuota <= 3.50
    except:
        return False
