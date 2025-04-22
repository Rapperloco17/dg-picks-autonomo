# Corrección de encoding para evitar errores 'surrogates not allowed'

def analizar_btts_local_vs_visitante(local_stats, visitante_stats):
    goles_local = local_stats.get("goals", {}).get("average", {}).get("home", 0)
    goles_visitante = visitante_stats.get("goals", {}).get("average", {}).get("away", 0)
    goles_encajados_local = local_stats.get("goals", {}).get("average", {}).get("against", 0)
    goles_encajados_visitante = visitante_stats.get("goals", {}).get("average", {}).get("against", 0)

    if goles_local >= 1.2 and goles_visitante >= 1.2 and goles_encajados_local >= 1.0 and goles_encajados_visitante >= 1.0:
        try:
            print("✅ BTTS con valor detectado".encode('utf-8', errors='ignore').decode('utf-8'))
        except Exception as e:
            print(f"Error en impresión: {e}")
        return True

    return False
