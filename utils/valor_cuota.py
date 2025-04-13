# utils/valor_cuota.py

def validar_valor_cuota(cuota):
    """
    Retorna True si la cuota tiene valor (entre 1.50 y 3.50), False si no.
    """
    try:
        cuota_float = float(cuota)
        return 1.50 <= cuota_float <= 3.50
    except ValueError:
        return False
