
# ... (todo el código anterior sin cambios en la lógica)

def evaluar_advertencia(pick, stats_local, stats_away):
    advertencia = ""
    if "Gana" in pick:
        if "Gana" in pick and "Empate" not in pick:
            equipo = pick.split("Gana ")[1].split(" @")[0]
            if equipo in stats_local["nombre"]:
                victorias = int(stats_local["forma"].split("G")[0])
                if victorias < 2:
                    advertencia = "⚠️ Ojo: el equipo local no viene en buena forma en casa."
            elif equipo in stats_away["nombre"]:
                victorias = int(stats_away["forma"].split("G")[0])
                if victorias < 2:
                    advertencia = "⚠️ Cuidado: el visitante no viene fuerte fuera de casa."
    return advertencia

if __name__ == "__main__":
    try:
        partidos = obtener_partidos_hoy()
        for p in partidos:
            cuotas_ml = obtener_cuotas_por_mercado(p["id_fixture"], 1)
            cuotas_ou = obtener_cuotas_por_mercado(p["id_fixture"], 5)
            cuotas_btts = obtener_cuotas_por_mercado(p["id_fixture"], 10)

            cuota_over = next((x["odd"] for x in cuotas_ou if "Over 2.5" in x["value"]), "❌")
            cuota_btts = next((x["odd"] for x in cuotas_btts if x["value"].lower() == "yes"), "❌")

            hora_mex, hora_esp = convertir_horas(p["hora_utc"])

            stats_local = obtener_estadisticas_equipo(p["home_id"], "local")
            stats_away = obtener_estadisticas_equipo(p["away_id"], "visitante")
            stats_local["nombre"] = p["local"]
            stats_away["nombre"] = p["visitante"]

            goles_local, goles_away = predecir_marcador(stats_local, stats_away)

            print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]}')
            print(f'🕐 Hora 🇲🇽 {hora_mex} | 🇪🇸 {hora_esp}')
            print(f'Cuotas: 🏠 {cuotas_ml[0]["odd"] if cuotas_ml else "❌"} | 🤝 {cuotas_ml[1]["odd"] if len(cuotas_ml)>1 else "❌"} | 🛫 {cuotas_ml[2]["odd"] if len(cuotas_ml)>2 else "❌"}')
            print(f'Over 2.5: {cuota_over} | BTTS: {cuota_btts}')
            print(f'📊 {p["local"]} (Local): GF {stats_local["gf"]} | GC {stats_local["gc"]} | Tiros {stats_local["tiros"]} | Posesión {stats_local["posesion"]}% | Forma: {stats_local["forma"]}')
            print(f'📊 {p["visitante"]} (Visitante): GF {stats_away["gf"]} | GC {stats_away["gc"]} | Tiros {stats_away["tiros"]} | Posesión {stats_away["posesion"]}% | Forma: {stats_away["forma"]}')
            print(f'🔮 Predicción marcador: {p["local"]} {goles_local} - {goles_away} {p["visitante"]}')
            pick = elegir_pick(p, goles_local, goles_away, cuotas_ml, cuota_over, cuota_btts)
            print(pick)
            advertencia = evaluar_advertencia(pick, stats_local, stats_away)
            if advertencia:
                print(advertencia)
            print("-" * 60)
    except Exception as e:
        print("❌ Error crítico. Se detiene la ejecución:")
        print(e)
