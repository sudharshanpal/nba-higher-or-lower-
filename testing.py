from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from nba_api.stats.static import players
import random

# impliment the selection later
# def choice():
#     user_choice = input("Do you want only active players? Y/N")
#     user_stat = input("Points, Rebounds, or Assists?")

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
        "total_assists": df["AST"].iloc[0].item()
    }
    return stats

def get_last_active_year(player_id):
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    df = info.common_player_info.get_data_frame()
    last_year = df.loc[0, "TO_YEAR"]
    return last_year



def higher_or_lower_points():
    while True:
        option1_id, option1_name = get_random_active_player_id()
        p1_totals = get_career_totals(option1_id)
        if p1_totals is not None:
            break

    while True:
        option2_id, option2_name = get_random_active_player_id()
        if option2_id == option1_id:
            continue
        p2_totals = get_career_totals(option2_id)
        if p2_totals is not None:
            break
    user_points = 0

    # main game loop
    while True:
        p1_points = p1_totals["total_points"]
        p2_points = p2_totals["total_points"]

        print("\nWho has MORE career points?")
        print(f"1) {option1_name}")
        print(f"2) {option2_name}")

        guess = input("Type 1 or 2 (or q to quit): ")

        if guess.lower() == "q":
            print("Thanks for playing!")
            break

        # make these buttons in the frontend
        if guess == "1":
            correct = p1_points >= p2_points
        elif guess == "2":
            correct = p2_points >= p1_points
        else:
            print("Invalid choice, try again.")
            continue

        if correct:
            user_points += 1
            print(f"correct, you have a {user_points} points")
        else:
            print(f"incorrect, you ended the game with {user_points} points")
            break

        print(f"{option1_name}: {p1_points} career points")
        print(f"{option2_name}: {p2_points} career points")

        option1_id, option1_name = option2_id, option2_name
        p1_totals = p2_totals

        while True:
            option2_id, option2_name = get_random_active_player_id()
            if option2_id == option1_id:
                continue
            p2_totals = get_career_totals(option2_id)
            if p2_totals is not None:
                break

higher_or_lower_points()
