def obtener_picks_tenis():
    # Esta función simula picks diarios con enfoque en rompimiento de servicio en el primer set
    picks = []

    # Simulación 1
    picks.append({
        'descripcion': 'Djokovic tiene buen desempeño al resto. Alcaraz vulnerable en su primer servicio.',
        'cuota': 1.75,
        'stake': '2/10',
        'canal': 'vip'
    })

    # Simulación 2
    picks.append({
        'descripcion': 'Medvedev ha generado múltiples oportunidades de quiebre en primeros sets.',
        'cuota': 2.10,
        'stake': '2/10',
        'canal': 'free'
    })

    # Simulación 3
    picks.append({
        'descripcion': 'Ruud ha concedido más de 4 break points en promedio en primeros sets.',
        'cuota': 1.85,
        'stake': '1/10',
        'canal': 'reto'
    })

    return picks

