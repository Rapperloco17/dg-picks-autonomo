```python
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Tennis Picks API")
API_KEY = os.getenv('MATCHSTAT_API_KEY')
BASE_URL = "https://api.matchstat.com/tennis"

class MatchRequest(BaseModel):
    match_id: str
    surface: str = "hard"

class PickResponse(BaseModel):
    player1_name: str
    player2_name: str
    break_probability: float
    predicted_winner: str

def fetch_api_data(endpoint: str, params: dict = None):
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error en API: {e}")

@app.post("/picks/")
async def generate_tennis_picks(match: MatchRequest):
    match_data = fetch_api_data(f"matches/{match.match_id}")
    if not match_data:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    
    player1 = match_data.get('player1', {'name': 'Player 1'})
    player2 = match_data.get('player2', {'name': 'Player 2'})
    surface = match.surface
    
    # Datos simulados (reemplazar con datos reales de la API)
    p1_break_pct = player1.get('break_pct', 0.30)
    p2_serve_2nd_win_pct = player2.get('serve_2nd_win_pct', 0.45)
    
    # Predicción simple de quiebre
    break_prob = p1_break_pct * (1 - p2_serve_2nd_win_pct) * (1.2 if surface == 'clay' else 0.8 if surface == 'grass' else 1)
    break_prob = min(break_prob, 0.99)
    
    # Predicción simple de ganador (basada en quiebres)
    winner = 'Player 1' if p1_break_pct > p2_serve_2nd_win_pct else 'Player 2'
    
    return PickResponse(
        player1_name=player1['name'],
        player2_name=player2['name'],
        break_probability=break_prob,
        predicted_winner=player1['name'] if winner == 'Player 1' else player2['name']
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```
