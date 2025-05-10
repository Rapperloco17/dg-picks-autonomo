import json
from utils.api_football import obtener_partidos_de_liga
from utils.cuotas import obtener_cuota_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol
from utils.telegram import enviar_mensaje
import datetime

def cargar_ligas():
    with open("utils/leagues_whitelist_ids.json", "r", encoding="utf-8") as f:
        return list(json.load(f).keys())

def generar_picks_futbol():
    hoy = datetime.date.today().strftime('%Y-%m-%d')
    temporada = "2024"

    ligas_ids = cargar_ligas()
    picks = []

    for liga_id in ligas_ids:
        partidos = obtener_partidos_de_liga(liga_id, hoy, temporada)

        for partido in partidos:
            fixture_id = partido["fixture"]["id"]
            cuotas = {}
            mercados = ["over_1.5", "over_2.5", "over_3.5", "under_2.5", "under_3.5", "1X", "X2", "12", "ML_local", "ML_visit", "Empate", "BTTS"]

            for mercado in mercados:
                cuota = obtener_cuota_fixture(fixture_id, mercado)
                if cuota:
                    cuotas[mercado] = cuota

            pick = analizar_partido_futbol(partido, {}, cuotas)

            if pick:
                picks.append(pick)

    for p in picks:
        mensaje = (
            f"⚽ {p['partido']}\n"
            f"📊 {p['pick']} @ {p['cuota']}\n"
            f"🧠 {p['motivo']}\n"
            f"✅ Valor detectado en la cuota"
        )
        enviar_mensaje(mensaje, canal='VIP')

if __name__ == "__main__":
    generar_picks_futbol()



