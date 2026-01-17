const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api' 
    : '/api';

let gameState = {
    player1_id: null,
    player1_name: null,
    player1_stats: null,
    player2_id: null,
    player2_name: null,
    player2_stats: null,
    stat_type: null,
    score: 0
};

let currentPlayer1Id = null;
let currentPlayer2Id = null;

function getPlayerHeadshotUrl(playerId) {
    return `https://stats.nba.com/media/players/230x185/${playerId}.png`;
}

async function preloadPlayerImage(playerId) {
    const imageSources = [
        `https://stats.nba.com/media/players/230x185/${playerId}.png`,
        `https://cdn.nba.com/headshots/nba/latest/1040x760/${playerId}.png`,
        `https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/${playerId}.png`
    ];
    
    return new Promise((resolve) => {
        let currentIndex = 0;
        
        function tryNextImage() {
            if (currentIndex >= imageSources.length) {
                console.warn(`All preload sources failed for player ${playerId}`);
                resolve(false);
                return;
            }
            
            const img = new Image();
            const currentUrl = imageSources[currentIndex];
            
            img.onload = function() {
                console.log(`Preloaded headshot for player ${playerId}`);
                resolve(true);
            };
            
            img.onerror = function() {
                currentIndex++;
                tryNextImage();
            };
            
            img.src = currentUrl;
        }
        
        tryNextImage();
    });
}

function setPlayerBackground(cardId, playerId, fallbackGradient) {
    const card = document.getElementById(cardId);
    
    const imageSources = [
        `https://stats.nba.com/media/players/230x185/${playerId}.png`,
        `https://cdn.nba.com/headshots/nba/latest/1040x760/${playerId}.png`,
        `https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/${playerId}.png`
    ];
    
    let currentIndex = 0;
    
    function tryNextImage() {
        if (currentIndex >= imageSources.length) {
            console.warn(`All headshot sources failed for player ${playerId}, using fallback gradient`);
            card.style.background = fallbackGradient;
            return;
        }
        
        const img = new Image();
        const currentUrl = imageSources[currentIndex];
        
        img.onload = function() {
            console.log(`Headshot loaded for player ${playerId} from source ${currentIndex + 1}`);
            card.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('${currentUrl}')`;
            card.style.backgroundSize = 'cover';
            card.style.backgroundPosition = 'center';
        };
        
        img.onerror = function() {
            console.warn(`Headshot failed for player ${playerId} from source ${currentIndex + 1}, trying next...`);
            currentIndex++;
            tryNextImage();
        };
        
        img.src = currentUrl;
        console.log(`Attempting source ${currentIndex + 1}: ${currentUrl}`);
    }
    
    tryNextImage();
}

async function startGame(statType) {
    try {
        const response = await fetch(`${API_URL}/start-game`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ stat_type: statType })
        });
        
        const data = await response.json();
        
        console.log('Game started with data:', data);
        
        // Store game state locally
        gameState = {
            player1_id: data.player1_id,
            player1_name: data.player1,
            player1_stats: data.player1_stats,
            player2_id: data.player2_id,
            player2_name: data.player2,
            player2_stats: data.player2_stats,
            stat_type: data.stat_type,
            score: data.score
        };
        
        currentPlayer1Id = data.player1_id;
        currentPlayer2Id = data.player2_id;
        
        console.log('Player IDs:', currentPlayer1Id, currentPlayer2Id);
        console.log('Player 1 stat value:', data.player1_stat_value);
        
        document.getElementById('setup-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'block';
        
        updateGameUI(data);
        
    } catch (error) {
        console.error('Error starting game:', error);
        alert('Failed to start game. Make sure the backend is running!');
    }
}

async function makeGuess(choice) {
    try {
        const buttons = document.querySelectorAll('.choice-btn');
        buttons.forEach(btn => btn.disabled = true);
        
        const guess = choice === 'higher' ? 2 : 1;
        
        const response = await fetch(`${API_URL}/submit-guess`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                guess: guess,
                player1_id: gameState.player1_id,
                player1_name: gameState.player1_name,
                player1_stats: gameState.player1_stats,
                player2_id: gameState.player2_id,
                player2_name: gameState.player2_name,
                player2_stats: gameState.player2_stats,
                stat_type: gameState.stat_type,
                score: gameState.score
            })
        });
        
        const data = await response.json();
        
        console.log('Received data:', data);
        
        document.getElementById('player2-stat-value').textContent = data.player2_stat.toLocaleString();
        document.getElementById('player2-stat-value').style.display = 'block';
        
        if (data.correct) {
            // Update game state
            gameState = {
                player1_id: data.player1_id,
                player1_name: data.player1,
                player1_stats: data.player1_stats,
                player2_id: data.player2_id,
                player2_name: data.player2,
                player2_stats: data.player2_stats,
                stat_type: gameState.stat_type,
                score: data.score
            };
            
            const newPlayer2Id = data.player2_id;
            await preloadPlayerImage(newPlayer2Id);
            
            const player1Card = document.getElementById('player1-card');
            const player2Card = document.getElementById('player2-card');
            
            document.getElementById('player1-name').textContent = data.player1;
            document.getElementById('player1-stat-value').textContent = data.player1_stat_value.toLocaleString();
            
            const statTypeText = gameState.stat_type ? gameState.stat_type.replace('total_', '') : 'points';
            document.getElementById('stat-description').textContent = `career ${statTypeText}`;
            
            currentPlayer1Id = data.player1_id;
            setPlayerBackground('player1-card', currentPlayer1Id, 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)');
            
            player1Card.classList.add('fade-out');
            player2Card.classList.add('slide-right-to-left');
            
            setTimeout(() => {
                currentPlayer2Id = data.player2_id;
                document.getElementById('player2-name').textContent = data.player2;
                document.getElementById('score').textContent = data.score;
                document.getElementById('player2-stat-value').style.display = 'none';
                
                setPlayerBackground('player2-card', currentPlayer2Id, 'linear-gradient(135deg, #16213e 0%, #0f3460 100%)');
      
                player1Card.classList.remove('fade-out');
                player2Card.classList.remove('slide-right-to-left');
                
                buttons.forEach(btn => btn.disabled = false);
            }, 600); 
            
        } else {
            setTimeout(() => {
                document.getElementById('game-screen').style.display = 'none';
                document.getElementById('gameover-screen').style.display = 'flex';
                document.getElementById('final-score').textContent = data.score;
                document.getElementById('final-stats').textContent = '';
            }, 1200);  
        }
        
    } catch (error) {
        console.error('Error making guess:', error);
        alert('Error processing guess!');
        const buttons = document.querySelectorAll('.choice-btn');
        buttons.forEach(btn => btn.disabled = false);
    }
}

async function quitGame() {
    if (!confirm('Are you sure you want to quit?')) {
        return;
    }
    
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('gameover-screen').style.display = 'flex';
    document.getElementById('final-score').textContent = gameState.score;
    document.getElementById('final-stats').textContent = '';
}

function updateGameUI(data) {
    console.log('=== Updating UI with data ===');
    console.log('Full data object:', JSON.stringify(data, null, 2));
    console.log('Current player IDs - P1:', currentPlayer1Id, 'P2:', currentPlayer2Id);
    
    document.getElementById('player1-name').textContent = data.player1;
    document.getElementById('player2-name').textContent = data.player2;
    document.getElementById('score').textContent = data.score;
    
    const statTypeText = data.stat_type ? data.stat_type.replace('total_', '') : 'points';
    document.getElementById('stat-description').textContent = `career ${statTypeText}`;
    
    const statElement = document.getElementById('player1-stat-value');
    console.log('Player1 stat value from data:', data.player1_stat_value, 'Type:', typeof data.player1_stat_value);
    
    if (data.player1_stat_value !== undefined && data.player1_stat_value !== null) {
        statElement.textContent = data.player1_stat_value.toLocaleString();
        statElement.style.display = 'block';
        console.log('Player 1 stat successfully set to:', statElement.textContent);
    } else {
        console.error('player1_stat_value is missing from data!');
        console.error('Data object:', data);
    }
    
    console.log('Setting backgrounds - Player1 ID:', currentPlayer1Id, 'Player2 ID:', currentPlayer2Id);
    
    if (currentPlayer1Id) {
        setPlayerBackground('player1-card', currentPlayer1Id, 'linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%)');
    } else {
        console.error('currentPlayer1Id is not set!');
    }
    
    if (currentPlayer2Id) {
        setPlayerBackground('player2-card', currentPlayer2Id, 'linear-gradient(135deg, #16213e 0%, #0a1628 100%)');
    } else {
        console.error('currentPlayer2Id is not set!');
    }
}

function restartGame() {
    document.getElementById('gameover-screen').style.display = 'none';
    document.getElementById('setup-screen').style.display = 'flex';
    
    gameState = {
        player1_id: null,
        player1_name: null,
        player1_stats: null,
        player2_id: null,
        player2_name: null,
        player2_stats: null,
        stat_type: null,
        score: 0
    };
    currentPlayer1Id = null;
    currentPlayer2Id = null;
}
