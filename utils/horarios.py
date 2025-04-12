
# utils/horarios.py

def obtener_hora_mlb():
    return "15:00"

def obtener_hora_nba():
    return "15:30"

def obtener_hora_futbol():
    return "11:00"

def dia_es_finde():
    from datetime import datetime
    return datetime.today().weekday() >= 5

def cada_dos_semanas():
    from datetime import datetime
    semana_actual = datetime.today().isocalendar()[1]
    return semana_actual % 2 == 0
