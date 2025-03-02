from match_parser import yield_match_data
import datetime


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
        assert len(players) == 5, f"Team {team_num} has {len(players)} players, expected 5 {game_data}"
    assert len(teams) == 2, f"Expected 2 teams, got {len(teams)}"

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

    player_ratings = {}
    for game_data in yield_match_data():
        calculate_elo(player_ratings, game_data)

    print(generate_leaderboard(player_ratings))






