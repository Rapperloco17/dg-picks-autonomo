def obtener_picks_tenis():
    # Picks simulados con análisis de rompimientos en el primer set
    picks = []

    picks.append({
        'partido': 'Djokovic vs Alcaraz',
        'pick': 'Djokovic rompe servicio en el 1er set',
        'cuota': 1.75,
        'stake': '2/10',
        'canal': 'vip',
        'analisis': 'Djokovic tiene buen desempeño al resto. Alcaraz vulnerable en su primer servicio.'
    })

    picks.append({
        'partido': 'Medvedev vs Zverev',
        'pick': 'Medvedev rompe servicio en el 1er set',
        'cuota': 2.10,
        'stake': '2/10',
        'canal': 'free',
        'analisis': 'Medvedev ha generado múltiples oportunidades de quiebre en primeros sets.'
    })

    picks.append({
        'partido': 'Ruud vs Sinner',
        'pick': 'Ruud NO rompe servicio en el 1er set',
        'cuota': 1.85,
        'stake': '1/10',
        'canal': 'reto',
        'analisis': 'Ruud ha concedido más de 4 break points en promedio en primeros sets.'
    })

    return picks

