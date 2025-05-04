import json
import os

def analizar_partido_futbol(datos, stats, cuotas):
    try:
        if not datos or not stats or not cuotas:
            return None

        equipo_local = datos.get("teams", {}).get("home", {}).get("name", "Local")
        equipo_visita = datos.get("teams", {}).get("away", {}).get("name", "Visitante")
        goles_local = stats.get("goles_local", 0)
        goles_visita = stats.get("goles_visita", 0)
        promedio_goles = (goles_local + goles_visita) / 2
        btts_prob = stats.get("btts_prob", 0)
        win_local = stats.get("prob_win_local", 0)
        win_visit = stats.get("prob_win_visit", 0)
        empate = stats.get("prob_draw", 0)

        opciones = []

        if "over_1.5" in cuotas and promedio_goles > 1.7 and cuotas["over_1.5"] >= 1.50:
            opciones.append({
                "pick": "Over 1.5 goles",
                "valor": True,
                "cuota": cuotas["over_1.5"],
                "motivo": "Promedio de goles alto en ambos equipos"
            })

        if "over_2.5" in cuotas and promedio_goles > 2.5 and cuotas["over_2.5"] >= 1.70:
            opciones.append({
                "pick": "Over 2.5 goles",
                "valor": True,
                "cuota": cuotas["over_2.5"],
                "motivo": "Equipos con tendencia a partidos con muchos goles"
            })

        if "over_3.5" in cuotas and promedio_goles > 3.2 and cuotas["over_3.5"] >= 2.00:
            opciones.append({
                "pick": "Over 3.5 goles",
                "valor": True,
                "cuota": cuotas["over_3.5"],
                "motivo": "Altísimo promedio goleador en ambos equipos"
            })

        if "under_3.5" in cuotas and promedio_goles < 3.5 and cuotas["under_3.5"] >= 1.60:
            opciones.append({
                "pick": "Under 3.5 goles",
                "valor": True,
                "cuota": cuotas["under_3.5"],
                "motivo": "Promedio de goles moderado o defensivo"
            })

        if "under_2.5" in cuotas and promedio_goles < 2.2 and cuotas["under_2.5"] >= 1.80:
            opciones.append({
                "pick": "Under 2.5 goles",
                "valor": True,
                "cuota": cuotas["under_2.5"],
                "motivo": "Promedio bajo de goles"
            })

        if "BTTS" in cuotas and btts_prob >= 65 and cuotas["BTTS"] >= 1.75:
            opciones.append({
                "pick": "Ambos equipos anotan",
                "valor": True,
                "cuota": cuotas["BTTS"],
                "motivo": "Alta probabilidad estadística de BTTS"
            })

        if "1X" in cuotas and win_local + empate > 70 and cuotas["1X"] >= 1.50:
            opciones.append({
                "pick": "Doble oportunidad 1X",
                "valor": True,
                "cuota": cuotas["1X"],
                "motivo": "Alta probabilidad de que el local no pierda"
            })

        if "X2" in cuotas and win_visit + empate > 70 and cuotas["X2"] >= 1.50:
            opciones.append({
                "pick": "Doble oportunidad X2",
                "valor": True,
                "cuota": cuotas["X2"],
                "motivo": "Alta probabilidad de que el visitante no pierda"
            })

        if "12" in cuotas and win_local + win_visit > 75 and cuotas["12"] >= 1.50:
            opciones.append({
                "pick": "Doble oportunidad 12",
                "valor": True,
                "cuota": cuotas["12"],
                "motivo": "Alta probabilidad de que haya un ganador"
            })

        if "ML_local" in cuotas and win_local > 60 and cuotas["ML_local"] >= 1.70:
            opciones.append({
                "pick": "Gana local",
                "valor": True,
                "cuota": cuotas["ML_local"],
                "motivo": "Alta probabilidad de victoria local"
            })

        if "ML_visit" in cuotas and win_visit > 60 and cuotas["ML_visit"] >= 1.80:
            opciones.append({
                "pick": "Gana visitante",
                "valor": True,
                "cuota": cuotas["ML_visit"],
                "motivo": "Alta probabilidad de victoria visitante"
            })

        if "Empate" in cuotas and empate > 30 and cuotas["Empate"] >= 3.00:
            opciones.append({
                "pick": "Empate",
                "valor": True,
                "cuota": cuotas["Empate"],
                "motivo": "Empate probable con valor en la cuota"
            })

        if opciones:
            mejor = sorted(opciones, key=lambda x: x["cuota"], reverse=True)[0]
            mejor["partido"] = f"{equipo_local} vs {equipo_visita}"

            archivo = "picks_futbol.json"
            if os.path.exists(archivo):
                with open(archivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []

            data.append(mejor)

            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            return mejor

        return None

    except Exception as e:
        print(f"Error en analizar_partido_futbol: {str(e)}")
        return None



