from utils.partidos_disponibles import obtener_partidos_disponibles
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.formato import formatear_pick
from utils.telegram import enviar_telegram
from utils.reto_stats import guardar_pick_generado
from datetime import datetime

def generar_picks_soccer(fecha_hoy: str):
    print(f"📅 Fecha actual: {fecha_hoy}")
    
    ligas = [2, 3, 39, 61, 78, 135, 140, 253, 262, 88, 94, 203, 1439]  # Ejemplo de whitelist reducida

    for liga_id in ligas:
        print(f"\n🔍 Analizando liga {liga_id} - temporada 2024")

        partidos = obtener_partidos_disponibles(liga_id=liga_id, fecha=fecha_hoy, temporada=2024)

        for partido in partidos:
            print(f"➡️ {partido['homeTeam']} vs {partido['awayTeam']}")

            resultado = analizar_partido_futbol(partido)

            if resultado["valor"]:
                print(f"✅ Pick encontrado: {resultado['pick']}")
                mensaje = formatear_pick(
                    deporte="fútbol",
                    tipo_apuesta=resultado["tipo"],
                    pick=resultado["pick"],
                    cuota=resultado["cuota"],
                    valor=resultado["valor"],
                    motivo=resultado["motivo"],
                    equipos=f"{partido['homeTeam']} vs {partido['awayTeam']}",
                    fecha=fecha_hoy
                )
                enviar_telegram(mensaje, canal="VIP")
                guardar_pick_generado("fútbol", resultado)

            else:
                print(f"❌ Sin valor en este partido: {resultado['motivo']}")



