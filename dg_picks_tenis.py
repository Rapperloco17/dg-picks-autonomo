```python
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
from typing import List, Optional

# Configuración de la API
app = FastAPI(title="Tennis Picks API")
API_KEY = os.getenv('MATCHSTAT_API_KEY')  # Obtener clave desde Railway
BASE_URL = "https://api.matchstat.com/tennis"  # Verifica en la documentación

# Modelo para los datos de entrada
class MatchRequest(BaseModel):
    match_id: str
    tournament: Optional[str] = None
    surface: Optional[str] = "hard"

# Modelo para la respuesta
class PickResponse(BaseModel):
    player1_name: str
    player2_name: str
    surface: str
    tournament: str
    break_probability: float
    predicted_winner: str
    set_win_probability: float
    total_games: float
    player1_stats: dict
    player2_stats: dict
    h2h: dict

# Función para obtener datos de la API
def fetch_api_data(endpoint: str, params: dict = None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con Matchstat API: {e}")

# Función para predecir probabilidad de quiebre en el primer set
def predict_break_probability(p1_break_pct: float, p2_serve_2nd_win_pct: float, surface: str) -> float:
    break_prob = p1_break_pct * (1 - p2_serve_2nd_win_pct)
    if surface == 'clay':
        break_prob *= 1.2
    elif surface == 'grass':
        break_prob *= 0.8
    return min(break_prob, 0.99)

# Función para predecir ganador del partido
def predict_match_winner(p1_form: float, p2_form: float, h2h_p1_wins: int, h2h_p2_wins: int, 
                         p1_odds: float, p2_odds: float, p1_break_pct: float, p2_break_pct: float,
                         p1_serve_1st_pct: float, p2_serve_1st_pct: float) -> str:
    score_p1 = (0.3 * p1_form + 
                0.2 * h2h_p1_wins / (h2h_p1_wins + h2h_p2_wins + 1) + 
                0.2 * (1 / p1_odds) + 
                0.2 * p1_break_pct + 
                0.1 * p1_serve_1st_pct)
    score_p2 = (0.3 * p2_form + 
                0.2 * h2h_p2_wins / (h2h_p1_wins + h2h_p2_wins + 1) + 
                0.2 * (1 / p2_odds) + 
                0.2 * p2_break_pct + 
                0.1 * p2_serve_1st_pct)
    return 'Player 1' if score_p1 > score_p2 else 'Player 2'

# Función para predecir probabilidad de ganar al menos un set
def predict_set_win(p1_break_pct: float, p1_serve_1st_pct: float, p2_serve_2nd_win_pct: float) -> float:
    set_win_prob = p1_break_pct + p1_serve_1st_pct - p2_serve_2nd_win_pct
    return min(set_win_prob, 0.95)

# Función para estimar número de juegos totales
def predict_total_games(surface: str, p1_odds: float, p2_odds: float) -> float:
    base_games_per_set = {'clay': 11, 'hard': 12, 'grass': 13}
    sets_expected = 2.5 if p1_odds < 1.6 or p2_odds < 1.6 else 2.8
    total_games = base_games_per_set.get(surface, 12) * sets_expected
    return round(total_games, 1)

# Endpoint para generar picks de un partido
@app.post("/picks/", response_model=PickResponse)
async def generate_tennis_picks(match: MatchRequest):
    match_data = fetch_api_data(f"matches/{match.match_id}")
    if not match_data:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    
    player1 = match_data.get('player1', {})
    player2 = match_data.get('player2', {})
    
    # Extraer datos (ajusta según la estructura real de la API)
    data = {
        'player1_name': player1.get('name', 'Player 1'),
        'player2_name': player2.get('name', 'Player 2'),
        'surface': match.surface or match_data.get('surface', 'hard'),
        'tournament': match.tournament or match_data.get('tournament', 'Desconocido'),
        'p1_serve_1st_pct': player1.get('serve_1st_pct', 0.65),
        'p1_serve_2nd_win_pct': player1.get('serve_2nd_win_pct', 0.50),
        'p1_break_pct': player1.get('break_pct', 0.30),
        'p2_serve_1st_pct': player2.get('serve_1st_pct', 0.67),
        'p2_serve_2nd_win_pct': player2.get('serve_2nd_win_pct', 0.45),
        'p2_break_pct': player2.get('break_pct', 0.28),
        'h2h_p1_wins': player1.get('h2h_wins', 1),
        'h2h_p2_wins': player2.get('h2h_wins', 1),
        'p1_form': player1.get('form', 0.8),
        'p2_form': player2.get('form', 0.7),
        'p1_odds': match_data.get('odds', {}).get('player1', 1.8),
        'p2_odds': match_data.get('odds', {}).get('player2', 2.0)
    }
    
    # Calcular predicciones
    break_prob = predict_break_probability(data['p1_break_pct'], data['p2_serve_2nd_win_pct'], data['surface'])
    winner = predict_match_winner(
        data['p1_form'], data['p2_form'], data['h2h_p1_wins'], data['h2h_p2_wins'],
        data['p1_odds'], data['p2_odds'], data['p1_break_pct'], data['p2_break_pct'],
        data['p1_serve_1st_pct'], data['p2_serve_1st_pct']
    )
    set_win_prob = predict_set_win(data['p1_break_pct'], data['p1_serve_1st_pct'], data['p2_serve_2nd_win_pct'])
    total_games = predict_total_games(data['surface'], data['p1_odds'], data['p2_odds'])
    
    # Preparar respuesta
    response = PickResponse(
        player1_name=data['player1_name'],
        player2_name=data['player2_name'],
        surface=data['surface'],
        tournament=data['tournament'],
        break_probability=break_prob,
        predicted_winner=f"{data['player1_name'] if winner == 'Player 1' else data['player2_name']}",
        set_win_probability=set_win_prob,
        total_games=total_games,
        player1_stats={
            'first_serve_pct': data['p1_serve_1st_pct'],
            'second_serve_win_pct': data['p1_serve_2nd_win_pct'],
            'break_pct': data['p1_break_pct'],
            'form': data['p1_form'],
            'odds': data['p1_odds']
        },
        player2_stats={
            'first_serve_pct': data['p2_serve_1st_pct'],
            'second_serve_win_pct': data['p2_serve_2nd_win_pct'],
            'break_pct': data['p2_break_pct'],
            'form': data['p2_form'],
            'odds': data['p2_odds']
        },
        h2h={'p1_wins': data['h2h_p1_wins'], 'p2_wins': data['h2h_p2_wins']}
    )
    
    return response

# Endpoint para obtener picks de múltiples partidos
@app.post("/picks/batch/", response_model=List[PickResponse])
async def generate_batch_tennis_picks(match_ids: List[str]):
    picks = []
    for match_id in match_ids:
        match_request = MatchRequest(match_id=match_id)
        pick = await generate_tennis_picks(match_request)
        picks.append(pick)
    return picks

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```
