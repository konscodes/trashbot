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
from datetime import datetime

custom_logger = logging.getLogger('custom')


def check_duty(file_path: str, specific_duty) -> tuple:
    '''Check who is on duty and return the team name, team id and members.
    file_path: data file with a list of teams
    specific_duty: duty to check e.g. "Garbage"
    '''
    with open(file_path) as file_object:
        data = json.load(file_object)
    teams = data['teams']
    for team_id, team in enumerate(teams):
        if specific_duty in team['duty']:
            team_name = team['name']
            members = [
                x['person']['english'] for x in team['rooms']
                if x['person']['english'] != ''
            ]
            return team_name, team_id, members, specific_duty
    custom_logger.error('Duty %s is not found.', specific_duty)
    return None, -1


def check_schedule(duties: list, duty: str) -> str:
    '''Return the duty schedule for a specific duty.
    duties: list of duties from data file
    duty: duty to check e.g. "Garbage"
    '''
    return [x['schedule'] for x in duties if x['name'] == duty]


def time_difference(start_time: object, end_time: object) -> tuple:
    '''Return the time difference between two dates in weeks and months'''
    difference = end_time - start_time
    weeks = difference.days // 7
    months = difference.days // 30
    return weeks, months


def rotate_index(index: int, number: int, list_length: int) -> int:
    '''Returns the new index as a result of rotating within the list range'''
    new_index = (index + number) % list_length
    if new_index >= list_length:
        new_index -= list_length
    return new_index


def rotate_duty(file_path: str, duty: str) -> tuple:
    '''Rotate the duty for the next team and write the updated data to file;
    Returns file path and specific duty.
    file_path: path to the json file
    duty: duty to rotate e.g. "Garbage"
    '''
    with open(file_path) as file_object:
        data = json.load(file_object)

    schedule = data['duties'][duty]
    team_on_duty, team_on_duty_id, members_on_duty, specific_duty = check_duty(
        file_path, duty)

    if team_on_duty:
        current = datetime.now()
        last = datetime.strptime(data['updated'], '%Y-%m-%d %H:%M:%S.%f')
        weeks, months = time_difference(last, current)
        if schedule == 'weekly':
            new_id = rotate_index(team_on_duty_id, weeks, len(data['teams']))
        elif schedule == 'monthly':
            new_id = rotate_index(team_on_duty_id, months, len(data['teams']))
        data['teams'][team_on_duty_id]['duty'].remove(duty)
        data['teams'][new_id]['duty'].append(duty)
        data['updated'] = str(current)
        with open(file_path, 'w') as file_object:
            json.dump(data, file_object, indent=2, ensure_ascii=False)
    return file_path, duty


if __name__ == '__main__':
    pass
