from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from nba_api.stats.static import players
import random
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def get_random_active_player_id():
    active_players = players.get_active_players()
    player = random.choice(active_players)
    return player["id"], player["full_name"]


def get_career_totals(player_id):
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    df = career.get_data_frames()[1]
    if df.empty:
        return None
    stats = {
        "total_points": df["PTS"].iloc[0].item(),
        "total_assists": df["AST"].iloc[0].item(),
        "total_rebounds": df["REB"].iloc[0].item()
    }
    return stats


class StartGameRequest(BaseModel):
    stat_type: str 


class GuessRequest(BaseModel):
    guess: int
    player1_id: int
    player1_name: str
    player1_stats: dict
    player2_id: int
    player2_name: str
    player2_stats: dict
    stat_type: str
    score: int


@app.post('/api/start-game')
def start_game(request: StartGameRequest):
    stat_choice = request.stat_type  

    if stat_choice == 'Points':
        stat_type = 'total_points'
    elif stat_choice == 'Assists':
        stat_type = 'total_assists'
    else:  
        stat_type = 'total_rebounds'
    
    while True:
        player1_id, player1_name = get_random_active_player_id()
        player1_stats = get_career_totals(player1_id)
        if player1_stats is not None:
            break
    while True:
        player2_id, player2_name = get_random_active_player_id()
        if player2_id == player1_id: 
            continue
        player2_stats = get_career_totals(player2_id)
        if player2_stats is not None:
            break
    
    return {
        'player1': player1_name,
        'player2': player2_name,
        'player1_id': player1_id,  
        'player2_id': player2_id,
        'player1_stats': player1_stats,
        'player2_stats': player2_stats,
        'player1_stat_value': player1_stats[stat_type],  
        'stat_type': stat_type,
        'score': 0
    }


@app.post('/api/submit-guess')
def submit_guess(request: GuessRequest):
    """Process user's guess - now stateless"""
    stat_type = request.stat_type
    
    player1_stat = request.player1_stats[stat_type]
    player2_stat = request.player2_stats[stat_type]
    
    old_player1_name = request.player1_name
    old_player2_name = request.player2_name
    
    if request.guess == 1:
        correct = player1_stat >= player2_stat
    else:  
        correct = player2_stat >= player1_stat
    
    if correct:
        score = request.score + 1
        
        # Player 2 becomes Player 1
        new_player1_id = request.player2_id
        new_player1_name = request.player2_name
        new_player1_stats = request.player2_stats
    
        # Get new Player 2
        while True:
            new_player2_id, new_player2_name = get_random_active_player_id()
            if new_player2_id == new_player1_id:
                continue
            new_player2_stats = get_career_totals(new_player2_id)
            if new_player2_stats is not None:
                break
        
        new_player1_stat_value = new_player1_stats[stat_type]
        
        return {
            'correct': True,
            'score': score,
            'player1': new_player1_name,  
            'player2': new_player2_name,
            'player1_id': new_player1_id,  
            'player2_id': new_player2_id,
            'player1_stats': new_player1_stats,
            'player2_stats': new_player2_stats,
            'player1_stat_value': new_player1_stat_value,  
            'old_player1': old_player1_name, 
            'old_player2': old_player2_name,
            'player1_stat': player1_stat,
            'player2_stat': player2_stat,
            'game_over': False
        }
    
    else:
        return {
            'correct': False,
            'score': request.score,
            'player1_stat': player1_stat,
            'player2_stat': player2_stat,
            'game_over': True,
            'player1': old_player1_name,
            'player2': old_player2_name
        }


@app.get("/")
def read_root():
    static_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return {"message": "Basketball Ordle API"}


# Vercel handler using Mangum
from mangum import Mangum
handler = Mangum(app)
