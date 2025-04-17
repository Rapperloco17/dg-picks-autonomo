from utils.sofascore import obtener_picks_tenis

def test_tenis():
    print("✅ Test DG Picks Tenis iniciado...\n")
    
    picks = obtener_picks_tenis()

    if not picks:
        print("⚠️ No se generaron picks de tenis en esta ejecución.")
    else:
        print(f"🎾 Total de picks generados: {len(picks)}\n")
        for i, pick in enumerate(picks, 1):
            print(f"--- Pick #{i} ---")
            print(f"📅 Partido: {pick['partido']}")
            print(f"📊 Análisis: {pick['analisis']}")
            print(f"💸 Cuota: {pick['cuota']}")
            print(f"⚖️ Stake: {pick['stake']}")
            print(f"📢 Canal: {pick['canal']}")
            print("✅ --------------------------\n")

if __name__ == "__main__":
    test_tenis()
