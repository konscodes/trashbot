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
import logging
custom_logger = logging.getLogger('custom')

def check_duty(file_path: str, specific_duty) -> tuple:
    '''Check who is on duty and return the team name and team id.
    file_path: data file with a list of teams
    specific_duty: duty to check e.g. "Garbage"
    '''
    with open(file_path) as file_object:
        data = json.load(file_object)
    teams = data['teams']
    for team_id, team in enumerate(teams):
        if specific_duty in team['duty']:
            custom_logger.debug(f"Team {team['name']} is on {specific_duty} duty.")
            custom_logger.debug(
                f"Members: {[x['person']['english'] for x in team['rooms']]}")
            return team['name'], team_id
    print(f"{specific_duty} duty is not found.")
    return None, -1


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

    team_on_duty, team_on_duty_id = check_duty(file_path, duty)
    if team_on_duty:
        data['teams'][team_on_duty_id]['duty'].remove(duty)
        if team_on_duty_id < len(data['teams']) - 1:
            data['teams'][team_on_duty_id + 1]['duty'].append(duty)
        else:
            data['teams'][0]['duty'].append(duty)

    with open(file_path, 'w') as file_object:
        json.dump(data, file_object, indent=2, ensure_ascii=False)
    return 'OK'


if __name__ == '__main__':
    pass
