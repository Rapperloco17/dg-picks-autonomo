
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_ID = "7450739156"

# Cargar dataset
with open("dataset_ml_base.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Convertir fechas a datetime y extraer año/mes/día como features
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df["año"] = df["fecha"].dt.year
df["mes"] = df["fecha"].dt.month
df["dia"] = df["fecha"].dt.day

# Features
X = df[["goles_local", "goles_visitante", "año", "mes", "dia"]]

# ---------------- Modelo Over 2.5 ----------------
y_over = df["over_2_5"]
X_train_o, X_test_o, y_train_o, y_test_o = train_test_split(X, y_over, test_size=0.2, random_state=42)
modelo_over25 = RandomForestClassifier(n_estimators=100, random_state=42)
modelo_over25.fit(X_train_o, y_train_o)
joblib.dump(modelo_over25, "modelo_over25.pkl")

# ---------------- Modelo BTTS ----------------
y_btts = df["btts"]
X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(X, y_btts, test_size=0.2, random_state=42)
modelo_btts = RandomForestClassifier(n_estimators=100, random_state=42)
modelo_btts.fit(X_train_b, y_train_b)
joblib.dump(modelo_btts, "modelo_btts.pkl")

print("✅ Modelos entrenados y guardados: modelo_over25.pkl y modelo_btts.pkl")

# Enviar por Telegram si hay token y usuario
def enviar_por_telegram(nombre_archivo):
    if TOKEN and USER_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
        with open(nombre_archivo, "rb") as file:
            response = requests.post(
                url,
                data={"chat_id": USER_ID},
                files={"document": file},
                timeout=30
            )
        if response.status_code == 200:
            print(f"✅ {nombre_archivo} enviado por Telegram.")
        else:
            print(f"⚠️ Error enviando {nombre_archivo}: {response.text}")

enviar_por_telegram("modelo_over25.pkl")
enviar_por_telegram("modelo_btts.pkl")
