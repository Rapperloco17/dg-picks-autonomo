
# 🤖 DG Picks Autónomo

Sistema automatizado para análisis y envío de picks deportivos por Telegram. Totalmente funcional para apuestas deportivas: tenis, NBA, MLB, fútbol, parlays, retos escalera y más.

---

## 🔧 Estructura del Proyecto

```
📁 utils/
├── telegram.py            # Envío de mensajes a Telegram
├── horarios.py            # Horarios programados por deporte
├── sofascore.py           # Datos simulados de partidos
├── valor_cuota.py         # Valida si una cuota tiene valor
📁 raíz/
├── main.py                # Orquestador general (automatización)
├── generador_tenis.py     # Picks de tenis
├── generador_mlb.py       # Picks de MLB
├── generador_nba.py       # Picks de NBA
├── generador_futbol.py    # Picks de fútbol
├── generador_parlay.py    # Parlay diario (VIP + Free)
├── generador_reto.py      # Reto Escalera (solo canal reto)
├── generador_mini_reto.py # Mini Reto Escalera (canal free)
```

---

## 📲 Canales de Telegram configurados

- 🔐 Canal VIP: `@dgpicksvippro`
- 🚀 Canal Reto Escalera: `@f2dqWWjYggJmM2Jh`
- 🎁 Canal Free: `@dgpicks17`

---

## 🕒 Automatización (main.py)

El sistema envía automáticamente todos los picks cada día:

| Deporte/Producto      | Hora México | Canal         |
|-----------------------|-------------|----------------|
| Tenis                | 10:00 a.m.  | VIP           |
| MLB                  | 14:00 p.m.  | VIP           |
| NBA                  | 14:00 p.m.  | VIP           |
| Fútbol               | 11:00 a.m.  | VIP           |
| Parlay Diario        | 12:00 p.m.  | VIP + FREE    |
| Reto Escalera        | 13:00 p.m.  | RETO          |
| Mini Reto Escalera   | 16:00 p.m.  | FREE          |

---

## 🚀 Instrucciones para correr

1. Subir todos los archivos a GitHub
2. Conectar tu repo en [Railway](https://railway.app/)
3. Asegurarte de tener los paquetes necesarios (`requests`, `schedule`)
4. Hacer deploy con `main.py` como punto de entrada

---

## 💡 Personalización futura

- Picks con imágenes o tickets
- Logs y seguimiento de rendimiento
- Control de duplicados y rotación
- Integración con base de datos

---

Hecho a medida para **DG Picks** ⚡
