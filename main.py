import csv
import os
import statsapi
import sys
import json

team_h_index = 0
team_v_index = 0
date_index = 0
game_no_h_index = 0
game_no_v_index = 0


games_played_on_date = {}

data = {}


team_abbreviations = None

if os.path.exists('player_data.json'):

    with open('player_data.json', 'r') as json_file:

        data = json.load(json_file)


def get_player_stats_for_curr_game(player_id, boxscore, team):

    player = boxscore['teams'][team]["players"][player_id]
    return player['stats']['batting']



def get_batting_order(game_id, team_type):
    # Fetch the game boxscore
    game_boxscore = statsapi.get('game_boxscore', {'gamePk': game_id})
    
    # Extract the team data
    team_data = game_boxscore['teams'][team_type]
    players = team_data['players']
    batting_order = []

    # Retrieve batting order from team data
    if 'battingOrder' in team_data:
        for player_id in team_data['battingOrder']:
            batting_order.append(f"ID{player_id}")

    return batting_order, game_boxscore


def get_team_abbreviations():

    team_abbreviations = {}

    with open('team_abbreviations.json', 'r') as json_file:
        team_abbreviations = json.load(json_file)

    return team_abbreviations

def get_starting_batters_stats(team_abbreviations, team_abbreviation, game_date, game_num, team_type, row_num):




    game_date_str = str(game_date)


    if len(team_abbreviations) == 0:
        sys.exit("Error: No team abbreviations found")

    team_name = team_abbreviations[team_abbreviation]

    team_id = statsapi.lookup_team(team_name)[0]['id']

    date_y_m_d = game_date_str[:4] + '-' + game_date_str[4:6] + '-' + game_date_str[6:]
    year_start_date = game_date_str[:4] + '-01-01'

    team_schedule = statsapi.schedule(date=date_y_m_d, team=team_id)

    game_id = None

    if game_date not in games_played_on_date:

        games_played_on_date[game_date] = {team_name: 1}
        game_id = team_schedule[0]['game_id']

    elif team_name not in games_played_on_date[game_date]:

        game_id = team_schedule[0]['game_id']
        games_played_on_date[game_date][team_name] = 1

    else:

        game_num = games_played_on_date[game_date][team_name]
        game_id = team_schedule[game_num]['game_id']
        games_played_on_date[game_date][team_name] += 1


    if game_id is None:
        sys.exit("Error: No game found")

    batting_order, game_boxscore = get_batting_order(game_id, team_type)

    for player_id in batting_order:
        player_stats = get_player_stats_for_curr_game(player_id, game_boxscore, team_type)

        hits = player_stats['hits']
        at_bats = player_stats['atBats']

        if row_num not in data:
            data[row_num] = {
                team_type: {
                    player_id : {
                        'team': team_name,
                        'game_date': game_date,
                        'game_num': game_num,
                        'hits': hits,
                        'at_bats': at_bats
                    }
                }
            }

        elif team_type not in data[row_num]:

            data[row_num][team_type] = {
                player_id : {
                    'team': team_name,
                    'game_date': game_date,
                    'game_num': game_num,
                    'hits': hits,
                    'at_bats': at_bats
                }
            }

        else:

            data[row_num][team_type][player_id] = {
                'team': team_name,
                'game_date': game_date,
                'game_num': game_num,
                'hits': hits,
                'at_bats': at_bats
            }



row_count = 0
total_row_count = 0
with open('df_bp9_new.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    total_row_count = sum(1 for _ in csvreader)

with open('df_bp9_new.csv', 'r') as csv_file:

    print("Opening CSV file")
    header_read = False
    csvreader = csv.reader(csv_file)

    line_count = 0

    new_rows = []


    for row in csvreader:

        current_row = row

        if header_read == False:

            team_h_index = row.index('team_h')
            team_v_index = row.index('team_v')
            game_no_h_index = row.index('game_no_h')
            game_no_v_index = row.index('game_no_v')
            date_index = row.index('date')

            header_read = True

        else:

            if line_count < len(data):

                print(f"Skipping row {line_count}")
                print(f"line_count: {line_count} len(data): {len(data)}")
                line_count += 1
                row_count += 1
                continue

            if team_abbreviations is None:

                team_abbreviations = get_team_abbreviations()

            get_starting_batters_stats(team_abbreviations, row[team_h_index], row[date_index], row[game_no_h_index], 'home', row_count)
            get_starting_batters_stats(team_abbreviations, row[team_v_index], row[date_index], row[game_no_v_index], 'away', row_count)

            line_count += 1
            row_count += 1

            if row_count % 100 == 0:

                with open('player_data.json', 'w') as json_file:

                    json.dump(data, json_file)

            print(f"Processed row {row_count} Total: {total_row_count}")
            print(f"Percentage complete: {round((row_count / total_row_count) * 100, 2)}%")
