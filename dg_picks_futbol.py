
import pandas as pd

# Lista de partidos y marcador tentativo calculado
partidos = [
    {"Partido": "Toluca vs Tigres UANL", "Marcador Tentativo": "2.3 - 1.1"},
    {"Partido": "Macara vs El Nacional", "Marcador Tentativo": "1.2 - 1.1"},
    {"Partido": "San Diego vs Sporting Kansas City", "Marcador Tentativo": "0.9 - 2.0"},
    {"Partido": "Portland Timbers vs Seattle Sounders", "Marcador Tentativo": "2.1 - 2.0"},
]

# Recomendaciones en base a lógica de goles esperados
def recomendar_apuesta(marcador):
    try:
        g1, g2 = map(float, marcador.split("-"))
    except:
        return "❌ Sin datos"

    total_goles = g1 + g2
    recomendaciones = []

    # ML
    if g1 - g2 >= 1:
        recomendaciones.append("🏆 Gana Local")
    elif g2 - g1 >= 1:
        recomendaciones.append("🏆 Gana Visitante")
    else:
        recomendaciones.append("🤝 Empate probable")

    # Over/Under
    if total_goles >= 2.8:
        recomendaciones.append("🔥 Over 2.5")
    elif total_goles <= 2.2:
        recomendaciones.append("🧊 Under 2.5")

    # BTTS
    if g1 >= 1 and g2 >= 1:
        recomendaciones.append("✅ BTTS (Ambos anotan)")

    return " | ".join(recomendaciones)

# Construcción del DataFrame
df = pd.DataFrame(partidos)
df["Recomendación"] = df["Marcador Tentativo"].apply(recomendar_apuesta)

# Generar formato estilo Telegram
df["Mensaje Telegram"] = df.apply(
    lambda row: f"🎯 *{row['Partido']}*\n🔢 Marcador tentativo: {row['Marcador Tentativo']}\n{row['Recomendación']}\n", axis=1
)

mensaje_final = "\n".join(df["Mensaje Telegram"].tolist())

print("📊 Análisis DG Picks – Recomendaciones del Día\n")
print(mensaje_final)
