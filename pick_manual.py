
from utils.telegram import enviar_mensaje

def enviar_pick_manual():
    print("🎯 Envío manual de pick personalizado")
    print("Selecciona el canal:")
    print("1. VIP")
    print("2. Reto Escalera")
    print("3. Free")

    canal_opcion = input("Opción de canal (1-3): ").strip()
    if canal_opcion == '1':
        canal = 'vip'
    elif canal_opcion == '2':
        canal = 'reto'
    elif canal_opcion == '3':
        canal = 'free'
    else:
        print("❌ Opción inválida.")
        return

    stake = input("Stake (ej. 2/10): ").strip()
    promocion = input("¿Es promocional? (s/n): ").strip().lower() == 's'

    mensaje = input("Escribe el mensaje completo del pick:
")

    final = f"{mensaje}\n🔥 Stake: {stake}"
    if promocion:
        final += "\n🎯 Pick promocional – DG Picks"

    enviar_mensaje(canal, final)
    print("✅ Pick enviado correctamente.")

if __name__ == '__main__':
    enviar_pick_manual()
