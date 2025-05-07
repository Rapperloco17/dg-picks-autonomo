import json
from utils.api_football import obtener_partidos_hoy, obtener_cuota_fixture
from utils.analizar_partido_futbol import analizar_partido_futbol

output_path = 'output/picks_futbol.json'

def generar_picks_futbol():
    print("Buscando partidos de hoy...")
    partidos = obtener_partidos_hoy()

    if not partidos:
        print("No se encontraron partidos disponibles para hoy.")
        return

    print(f"Total de partidos encontrados: {len(partidos)}")
    picks_generados = []

    for partido in partidos:
        analisis = analizar_partido_futbol(partido)
        if analisis:
            cuota = obtener_cuota_fixture(partido['fixture']['id'], analisis['mercado'])
            if cuota:
                analisis['cuota'] = cuota
                picks_generados.append(analisis)

    if picks_generados:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(picks_generados, f, indent=4, ensure_ascii=False)

        print(f"\n✅ Se generaron {len(picks_generados)} picks con valor:\n")
        for pick in picks_generados:
            print(f"{pick['partido']} | {pick['mercado']} @ {pick['cuota']} → {pick['razon']}")
    else:
        print("No se generó ningún pick con valor para hoy.")

if __name__ == '__main__':
    generar_picks_futbol()


