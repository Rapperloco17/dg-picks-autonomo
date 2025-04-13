from datetime import datetime, timedelta

# 🕒 Horarios estimados para cada deporte

def obtener_hora_mlb():
    return "14:00"  # Puedes ajustar a 5 horas antes del primer juego

def obtener_hora_nba():
    return "14:00"  # Ajustar según hora local si cambia

def obtener_hora_futbol():
    return "11:00"  # 2 horas antes del primer partido del día

# 📅 Validación de fines de semana
def dia_es_finde():
    return datetime.now().weekday() in [5, 6]  # 5 = sábado, 6 = domingo

# 📆 Reto mini escalera cada 2 semanas
def cada_dos_semanas():
    # Asume que la semana 1 del año es de inicio
    semana_actual = datetime.now().isocalendar()[1]
    return semana_actual % 2 == 1
