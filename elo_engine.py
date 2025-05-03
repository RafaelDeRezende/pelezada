from match_parser import yield_match_data
import datetime
import itertools
from typing import List, Dict, Tuple

_guest_players = ['Ben Ben', 'Dzmitry']


def build_teams(players: List[str], player_ratings: Dict[str, int], num_teams: int = 2) -> Tuple[List[List[str]], float]:
    """
    Build balanced teams based on player ELO ratings.

    Args:
        players: List of player names loaded from the file
        player_ratings: Dictionary mapping player names to their ELO ratings
        num_teams: Number of teams (2 or 3), default is 2

    Returns:
        Tuple containing the best team combination and the minimum ELO difference

    Raises:
        ValueError: If num_teams is not 2 or 3, or if the number of players is incorrect
    """
    # Validate number of teams
    if num_teams not in [2, 3]:
        raise ValueError("Number of teams must be 2 or 3")

    # Check if the number of players matches the requirement
    required_players = 5 * num_teams
    if len(players) != required_players:
        raise ValueError(f"Expected {required_players} players for {num_teams} teams, got {len(players)}")

    # Add missing players with default ELO of 1000
    for player in players:
        if player not in player_ratings:
            player_ratings[player] = 975
            print(f"Player {player} not found in player_ratings, adding with 975 ELO")

    # Helper function to calculate team ELO
    def team_elo(team):
        return sum(player_ratings[p] for p in team)

    best_teams = None
    min_diff = float('inf')

    if num_teams == 2:
        # Generate all possible team 1 combinations (5 players)
        for team1 in itertools.combinations(players, 5):
            team1 = list(team1)
            team2 = [p for p in players if p not in team1]
            elo1 = team_elo(team1)
            elo2 = team_elo(team2)
            diff = abs(elo1 - elo2)
            if diff < min_diff:
                min_diff = diff
                best_teams = [team1, team2]
    elif num_teams == 3:
        # Generate all possible team 1 and team 2 combinations
        for team1 in itertools.combinations(players, 5):
            team1 = list(team1)
            remaining = [p for p in players if p not in team1]
            for team2 in itertools.combinations(remaining, 5):
                team2 = list(team2)
                team3 = [p for p in remaining if p not in team2]
                elo1 = team_elo(team1)
                elo2 = team_elo(team2)
                elo3 = team_elo(team3)
                diff = max(elo1, elo2, elo3) - min(elo1, elo2, elo3)
                if diff < min_diff:
                    min_diff = diff
                    best_teams = [team1, team2, team3]

    return best_teams, min_diff




def calculate_elo(player_ratings, game_data, k_factor=32):
    """
    Calculate ELO for players based on the parsed game result with score impact.

    Args:
    - player_ratings (dict): {player_name: current_elo}
    - game_data (dict): structured data from parse_game_data.
    - k_factor (int): Determines ELO change magnitude.

    Returns:
    - Updated player_ratings (dict)
    """
    teams = game_data['teams']

    for team_num, players in teams.items():
        assert len(players) == len(set(players)), f"Duplicate players in team {team_num}"
    assert len(teams) == 2, f"Expected 2 teams, got {len(teams)}"

    # Assert both teams have the same number of players

    teams_keys = list(teams.keys())

    assert len(teams[teams_keys[0]]) == len(teams[teams_keys[1]]), "Both teams must have the same number of players"


    print(teams)
    result = game_data['result']
    print(result)
    winning_team = result['winning_team']
    score_diff = int(result['score'])  # Score is already parsed as int

    # Determine score multiplier
    if 3 > score_diff > 0:
        score_multiplier = 1      # Simple win
    elif 3 <= score_diff < 5:
        score_multiplier = 1.5    # Strong win
    elif score_diff >= 5:
        score_multiplier = 2      # Massacre
    else:
        score_multiplier = 0 # draw


    # Calculate average ELO per team
    team_elos = {}
    for team_num, players in teams.items():
        total_elo = sum(player_ratings.get(p, 1000) for p in players)
        team_elos[team_num] = total_elo / len(players)

    # Apply ELO calculation for each player
    for team_num, players in teams.items():
        actual_result = 1 if team_num == winning_team else 0
        opponent_team = [num for num in teams if num != team_num][0]
        expected_score = 1 / (1 + 10 ** ((team_elos[opponent_team] - team_elos[team_num]) / 400))

        # Adjust based on score impact
        for player in players:
            current_elo = player_ratings.get(player, 1000)
            elo_change = k_factor * (actual_result - expected_score) * score_multiplier
            new_elo = current_elo + elo_change
            player_ratings[player] = round(new_elo, 2)

    return player_ratings

def generate_leaderboard(player_ratings):
    """
    Generates a WhatsApp-friendly leaderboard, handling ties and rounding ELOs.

    Args:
      - player_ratings (dict): {player_name: elo}

    Returns:
      - str: Formatted leaderboard string.
    """
    # Round ELO scores
    rounded_ratings = {player: round(elo) for player, elo in player_ratings.items()}

    # Remove guest players from leaderboard
    for guest_player in _guest_players:
        if guest_player in rounded_ratings:
            del rounded_ratings[guest_player]

    # Remove players with name containing Krank
    for player in list(rounded_ratings.keys()):
        if 'Krank' in player:
            del rounded_ratings[player]

    # Sort players by ELO (highest first)
    sorted_players = sorted(rounded_ratings.items(), key=lambda x: x[1], reverse=True)

    leaderboard = ["🏆 *Pelezada Leaderboard* 🏆", "-----------------------------"]
    # We use rank-based medals (competition style).
    # That way if two players tie for rank=1, they both get gold,
    # the next player is rank=3, and gets bronze.
    medals_by_rank = {1: "🥇", 2: "🥈", 3: "🥉"}

    last_elo = None
    rank = 0              # Current rank displayed
    actual_position = 0   # Position in the sorted list (1-based)

    for player, elo in sorted_players:
        actual_position += 1

        # Only update rank if a new ELO appears (no tie)
        if elo != last_elo:
            rank = actual_position

        # Determine whether to display medal or rank number
        rank_display = medals_by_rank.get(rank, f"{rank}.")
        leaderboard.append(f"{rank_display} {player} - {elo} ELO")

        last_elo = elo

    leaderboard.append("-----------------------------")
    # add today date
    leaderboard.append(f"📅 {datetime.datetime.now().strftime('%d/%m/%Y')}")

    return "\n".join(leaderboard)

if __name__ == '__main__':

    generate_learderboard = True
    num_teams = 2

    # These players get an initial ELO of 950 (not to overly unbalance the teams)
    player_ratings = {
        "Gio": 950,
        "Marcelo B": 950,
    }
    for game_data in yield_match_data():
        calculate_elo(player_ratings, game_data)

    if generate_learderboard:
        print(generate_leaderboard(player_ratings))
    else:
        with open('team_builder/players.txt', 'r') as file:
            players = file.read().splitlines()
        print(len(players))
        teams = build_teams(players, player_ratings, num_teams=num_teams)


        elo_avg = sum([player_ratings[player] for player in teams[0][0]]) / 5
        print(f"Team 1 ELO: {elo_avg}")
        print("### Team 1 ### - ELO: ", int(elo_avg))


        for player in teams[0][0]:
            print(f"{player}")

        elo_avg = sum([player_ratings[player] for player in teams[0][1]]) / 5
        print("### Team 2 ### - ELO: ", int(elo_avg))
        for player in teams[0][1]:
            print(f"{player}")

        if num_teams == 3:
            elo_avg = sum([player_ratings[player] for player in teams[0][2]]) / 5
            print("### Team 3 ### - ELO: ", int(elo_avg))
            for player in teams[0][2]:
                print(f"{player}")









