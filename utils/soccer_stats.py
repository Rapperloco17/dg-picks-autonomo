# utils/soccer_stats.py

from utils.valor_cuota import obtener_cuota_real
from utils.api_football import obtener_stats_partido

def analizar_partido(partido):
    equipo_local = partido['teams']['home']['name']
    equipo_visitante = partido['teams']['away']['name']
    fixture_id = partido['fixture']['id']

    stats = obtener_stats_partido(fixture_id)
    if not stats:
        return None

    goles_local = partido['goals']['home']
    goles_visitante = partido['goals']['away']
    form_local = partido['form']['local']
    form_visitante = partido['form']['visitante']

    promedio_goles = form_local['promedio_goles'] + form_visitante['promedio_goles']
    tiros_local = form_local['promedio_tiros']
    tiros_visitante = form_visitante['promedio_tiros']

    # Analizar posibles apuestas
    picks = []

    # ML Local
    if form_local['racha'] == 'W' and form_visitante['racha'] == 'L':
        cuota_ml = obtener_cuota_real(fixture_id, '1')
        if cuota_ml and cuota_ml <= 1.80:
            picks.append({
                'mercado': 'ML',
                'pick': f'Gana {equipo_local}',
                'cuota': cuota_ml,
                'analisis': f"{equipo_local} llega con buena racha, {equipo_visitante} viene flojo."
            })

    # Over 2.5 goles
    if promedio_goles >= 2.7:
        cuota_ov25 = obtener_cuota_real(fixture_id, 'over_2.5')
        if cuota_ov25:
            picks.append({
                'mercado': 'Over 2.5 goles',
                'pick': 'Over 2.5 goles',
                'cuota': cuota_ov25,
                'analisis': f"Promedio de goles alto entre ambos equipos: {promedio_goles:.2f}"
            })

    # Over 1.5 o 3.5 según lógica
    if promedio_goles <= 1.8:
        cuota_ov15 = obtener_cuota_real(fixture_id, 'over_1.5')
        if cuota_ov15:
            picks.append({
                'mercado': 'Over 1.5 goles',
                'pick': 'Over 1.5 goles',
                'cuota': cuota_ov15,
                'analisis': f"A pesar del promedio bajo, se espera reacción ofensiva."
            })
    elif promedio_goles >= 3.5:
        cuota_ov35 = obtener_cuota_real(fixture_id, 'over_3.5')
        if cuota_ov35:
            picks.append({
                'mercado': 'Over 3.5 goles',
                'pick': 'Over 3.5 goles',
                'cuota': cuota_ov35,
                'analisis': f"Equipos ofensivos con tendencia clara a juegos abiertos."
            })

    # Doble oportunidad
    if form_local['solidez'] and not form_visitante['constante']:
        cuota_doble = obtener_cuota_real(fixture_id, '1X')
        if cuota_doble and cuota_doble <= 1.70:
            picks.append({
                'mercado': 'Doble oportunidad',
                'pick': f'{equipo_local} o Empate',
                'cuota': cuota_doble,
                'analisis': f"{equipo_local} suele sacar puntos en casa, visitante irregular."
            })

    return picks
