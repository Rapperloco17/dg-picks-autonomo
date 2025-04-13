from utils.telegram import TELEGRAM_BOT_TOKEN
import requests

# Aquí pon el username público del canal VIP (sin @)
username = "dgpickspro17"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChat?chat_id=@{username}"

response = requests.get(url)
data = response.json()

print(data)

