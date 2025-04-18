import json
import os
from datetime import datetime

# Ya existente

def interpretar_resultado_pick(pick, resultado):
    if not resultado:
        return "desconocido"

    tipo = pick.get("tipo")
    goles_local = resultado.get("goles_local", 0)
    goles_visita = resultado.get("goles_visita", 0)
    total_goles = goles_local + goles_visita

    # Normalizar nombres de equipos
    equipo_pick = pick.get("equipo", "").lower()
    local = resultado.get("nombre_local", "").lower()
    visita = resultado.get("nombre_visita", "").lower()

    if tipo == "ML":
        if equipo_pick in local and goles_local > goles_visita:
            return "ganado"
        elif equipo_pick in visita and goles_visita > goles_local:
            return "ganado"
        else:
            return "perdido"

    elif tipo == "OVER":
        linea = float(pick.get("linea", 2.5))
        return "ganado" if total_goles > linea else "perdido"

    elif tipo == "UNDER":
        linea = float(pick.get("linea", 2.5))
        return "ganado" if total_goles < linea else "perdido"

    elif tipo == "BTTS":  # Ambos anotan
        return "ganado" if goles_local > 0 and goles_visita > 0 else "perdido"

    return "desconocido"

# NUEVAS FUNCIONES PARA SOPORTE AL GENERADOR

def analyze_match(partido):
    return {
        "valor": True,
        "cuota": partido.get("cuota", 1.85),
        "stake": 1,
        "analisis": "Análisis simulado. Partido con valor.",
        "porcentaje_btts": 60,
        "prom_goles": 2.7,
        "prom_corners": 8.2,
        "prom_tarjetas": 4.0
    }

def get_soccer_matches(api_key, whitelist):
    # Simulación para evitar errores. Luego se reemplaza por API real
    return [
        {
            "partido": "Barcelona vs Sevilla",
            "equipo_local": "Barcelona",
            "equipo_visitante": "Sevilla",
            "liga": "La Liga",
            "cuota": 1.85
        }
    ]
