'''
Basic json data manipulation example.
This snippet shows how to read and write json data.
- The json data is stored in a file files/teams.json.
- The json data is read and stored in a dictionary.
- Function is called to search the dictionary for a specific duty.
    - Print the team name and the team members.
    - Remove the duty for the team.
    - Add the duty for the next team in the dictionary.
- Write the dictionary back to the json file.
'''
import json

def check_duty(teams: list, specific_duty) -> tuple:
    '''Check who is on duty and return the team name and team id.
    teams: list of teams from data file
    specific_duty: duty to check e.g. "Garbage"
    '''
    for team_id, team in enumerate(teams):
        if specific_duty in team['duty']:
            print(f"Team {team['name']} is on {specific_duty} duty.")
            print(f"Members: {[x['person']['english'] for x in team['rooms']]}")
            return team['name'], team_id 
    print(f"{specific_duty} duty is not found.")
    return None, -1


def update_duty(teams: list, duty: str) -> list:
    '''Rotate the duty for the next team and returns the updated teams list.
    teams: list of teams from data file
    duty: duty to rotate e.g. "Garbage"
    '''
    team_on_duty, team_on_duty_id = check_duty(teams, duty)
    if team_on_duty:
        teams[team_on_duty_id]['duty'].remove(duty)
        if team_on_duty_id < len(teams) - 1:
            teams[team_on_duty_id + 1]['duty'].append(duty)
        else:
            teams[0]['duty'].append(duty)
        return teams
    print('No duty to rotate.')
    return teams


def check_schedule(duties: list, duty: str) -> str:
    '''Return the duty schedule for a specific duty.
    duties: list of duties from data file
    duty: duty to check e.g. "Garbage"
    '''
    return [x['schedule'] for x in duties if x['name'] == duty]


def rotate_duty(file_path: str, duty: str) -> None:
    '''Rotate the duty for the next team and write the updated data to file.
    file_path: path to the json file
    duty: duty to rotate e.g. "Garbage"
    '''
    with open(file_path) as file_object:
        data = json.load(file_object)
    updated_roster = update_duty(data['teams'], duty)
    data['teams'] = updated_roster
    with open(file_path, 'w') as file_object:
        json.dump(data, file_object, indent=2, ensure_ascii=False)
    return 'OK'


if __name__ == '__main__':
    import os

    PATENT_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE = os.path.dirname(PATENT_DIR) + '/files/data.json'

    # Read the json data from the file.
    with open(FILE) as file_object:
        data = json.load(file_object)

    updated_roster = update_duty(data['teams'], 'Groceries')
    data['teams'] = updated_roster
    print(check_schedule(data['duties'], 'Garbage'))

    # Write the dictionary back to the json file.
    with open(FILE, 'w') as file_object:
        json.dump(data, file_object, indent=2, ensure_ascii=False)
