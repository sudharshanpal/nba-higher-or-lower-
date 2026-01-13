from fastapi import FastAPI, HTTPException, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from nba_api.stats.static import players
import random
import os
from dotenv import load_dotenv
import uuid
from typing import Optional

load_dotenv()

app = FastAPI()

# need to add url after vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

sessions = {}  

def get_random_active_player_id():
    active_players = players.get_active_players()
    player = random.choice(active_players)
    print(player)
    return player["id"], player["full_name"]


def get_career_totals(player_id):

    career = playercareerstats.PlayerCareerStats(player_id=player_id)

    df = career.get_data_frames()[1]
    if df.empty:
        return None
    stats = {
        # the .item() makes it go from np.int64(number) to number
        "total_points": df["PTS"].iloc[0].item(),
        "total_assists": df["AST"].iloc[0].item(),
        "total_rebounds": df["REB"].iloc[0].item()
    }
    return stats

def get_last_active_year(player_id):
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    df = info.common_player_info.get_data_frame()
    last_year = df.loc[0, "TO_YEAR"]
    return last_year

class StartGameRequest(BaseModel):
    stat_type: str 

# 1 for player 1, 2 for player 2
class GuessRequest(BaseModel):
    guess: int  
    session_id: str


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
        # skips if the same player is chosen 
        if player2_id == player1_id: 
            continue
        player2_stats = get_career_totals(player2_id)
        if player2_stats is not None:
            break
    
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        'player1_id': player1_id,
        'player1_name': player1_name,
        'player1_stats': player1_stats,
        'player2_id': player2_id,
        'player2_name': player2_name,
        'player2_stats': player2_stats,
        'stat_type': stat_type,
        'score': 0
    }
    
    return {
        'session_id': session_id,  
        'player1': player1_name,
        'player2': player2_name,
        'player1_id': player1_id,  
        'player2_id': player2_id,
        'player1_stat_value': player1_stats[stat_type],  
        'stat_type': stat_type,
        'score': 0
    }


@app.post('/api/submit-guess')
def submit_guess(request: GuessRequest):
    """Process user's guess - COMPLETED"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game = sessions[request.session_id]
    stat_type = game['stat_type']
    
    player1_stat = game['player1_stats'][stat_type]
    player2_stat = game['player2_stats'][stat_type]
    
    old_player1_name = game['player1_name']
    old_player2_name = game['player2_name']
    
    if request.guess == 1:
        correct = player1_stat >= player2_stat
    else:  
        correct = player2_stat >= player1_stat
    
    if correct:
        game['score'] += 1
        
        game['player1_id'] = game['player2_id']
        game['player1_name'] = game['player2_name']
        game['player1_stats'] = game['player2_stats']
    
        while True:
            new_player2_id, new_player2_name = get_random_active_player_id()
            if new_player2_id == game['player1_id']:
                continue
            new_player2_stats = get_career_totals(new_player2_id)
            if new_player2_stats is not None:
                break
        
        game['player2_id'] = new_player2_id
        game['player2_name'] = new_player2_name
        game['player2_stats'] = new_player2_stats
        
        new_player1_stat_value = game['player1_stats'][stat_type]
        
        return {
            'correct': True,
            'score': game['score'],
            'player1': game['player1_name'],  
            'player2': game['player2_name'],
            'player1_id': game['player1_id'],  
            'player2_id': game['player2_id'],
            'player1_stat_value': new_player1_stat_value,  
            'old_player1': old_player1_name, 
            'old_player2': old_player2_name,
            'player1_stat': player1_stat,
            'player2_stat': player2_stat,
            'game_over': False
        }
    
    else:
        final_score = game['score']
        del sessions[request.session_id]
        
        return {
            'correct': False,
            'score': final_score,
            'player1_stat': player1_stat,
            'player2_stat': player2_stat,
            'game_over': True,
            'player1': old_player1_name,
            'player2': old_player2_name
        }


@app.get('/api/get-score/{session_id}')
def get_score(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {'score': sessions[session_id]['score']}


class QuitGameRequest(BaseModel):
    session_id: str


@app.post('/api/quit-game')
def quit_game(request: QuitGameRequest):
    """End the game early - COMPLETED"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    final_score = sessions[request.session_id]['score']
    del sessions[request.session_id]
    
    return {
        'game_over': True,
        'score': final_score
    }

# @app.get("/")
# def read_root():
#     return FileResponse('static/index.html')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
