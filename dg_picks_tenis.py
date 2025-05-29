import requests

API_KEY = "62445b378b11906da093a6ae6513242ae3de2134660c3aefbf74872bbcdccdc2"
BASE_URL = "https://api.api-tennis.com"
url = f"{BASE_URL}/tennis/?method=get_matches&date=2025-05-28&category=ATP,Challenger&APIkey={API_KEY}"

response = requests.get(url)

print("Status code:", response.status_code)
print("Texto recibido:")
print(response.text)
