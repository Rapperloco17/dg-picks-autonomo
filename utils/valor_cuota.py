def filtrar_cuotas_con_valor(cuotas):
    """
    Filtra una lista de picks con base en el atributo "valor".
    Solo conserva las que tienen valor = True y cuota entre 1.50 y 3.50.
    """
    cuotas_filtradas = []

    for cuota in cuotas:
        valor = cuota.get("valor", False)
        cuota_num = float(cuota.get("cuota", 0))

        if valor and 1.50 <= cuota_num <= 3.50:
            cuotas_filtradas.append(cuota)

    return cuotas_filtradas
