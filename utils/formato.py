
# utils/formato.py

def formatear_pick(partido, analisis, deporte="tenis", reto_escalera=False, paso=None):
    texto = f"🎾 *{deporte.upper()}* - {partido.get('jugador1', 'Jugador A')} vs {partido.get('jugador2', 'Jugador B')}"
    texto += f"\n✅ Análisis: {analisis.get('descripcion', 'Análisis detallado.')}"
    if paso:
        texto = f"🔁 *Paso {paso}*\n" + texto
    return texto

def formatear_parlay(picks, cuota_minima=2.0):
    if not picks:
        return None
    texto = "🔥 *Parlay del Día* 🔥\n"
    for i, pick in enumerate(picks):
        texto += f"{i+1}. {pick}\n"
    texto += f"\n💰 Cuota combinada: {cuota_minima}"
    texto += "\nStake recomendado: 2/10"
    return texto
