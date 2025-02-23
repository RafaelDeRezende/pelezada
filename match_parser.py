import os
from datetime import datetime

DIRPATH = './matches'

def list_match_in_directory():
    return [f for f in os.listdir(DIRPATH) if f.endswith('.txt')]


def parse_game_data(file_content):
    """
    Parses the game data into structured format, grouping players by team.

    Args:
    - file_content (str): Raw file data.

    Returns:
    - dict with 'teams', 'date', and 'result'.
    """
    teams = {}
    game_date = None
    result = None

    lines = file_content.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('date'):
            # Extract and parse date
            date_str = line.split(' ')[1]
            game_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        elif line.startswith('result'):
            # Extract result
            result_parts = line.split('-')
            winning_team = int(result_parts[1].strip())
            score = int(result_parts[2].strip())
            result = {'winning_team': winning_team, 'score': score}
        elif '-' in line:
            # Extract player and team, structure by team
            parts = line.split('-')
            player_name = parts[0].strip()
            team_number = int(parts[1].strip())
            if team_number not in teams:
                teams[team_number] = []
            teams[team_number].append(player_name)

    game_data = {
        'teams': teams,
        'date': game_date,
        'result': result
    }

    return game_data

def yield_match_data():
    for files in  list_match_in_directory():
        file_path = os.path.join(DIRPATH, files)
        with open(file_path, 'r') as file:
            file_content = file.read()
        match_data = parse_game_data(file_content)
        yield match_data

