'''This bot will send a reoccurring reminders on garbage collection schedule'''
import json
import logging
import logging.config
import os

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,
                            JoinEvent, SourceGroup)
import roster

# Create a new Flask instance
app = Flask(__name__)

# Line API requires a token for access and handler needs secret
line_bot_api = LineBotApi(str(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')))
handler = WebhookHandler(str(os.environ.get('LINE_CHANNEL_SECRET')))
scheduler = BackgroundScheduler()

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = BASE_DIR + '/logs/logger.log'
ROSTER_PATH = BASE_DIR + '/roster_data.json'

# Set constants
COMMANDS = {
    '!help': {
        'description': 'Show available commands',
        'text': 'Here is the list of all commands: '
    },
    '!start': {
        'description': 'Start the scheduler',
        'text': 'かしこまりました！\nLet me set your schedule.'
    },
    '!stop': {
        'description': 'Pause the scheduler',
        'text': 'かしこまりました！\nPausing the rotation for now.'
    },
    '!duty': {
        'description': 'Report who is on duty'
    }
}
DUTIES = {"Groceries": "monthly", "Garbage": "weekly"}
group_info = {'id': None, 'name': ''}

# Read JSON and configure logging using dictionary
with open(BASE_DIR + '/logging_conf.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    data['handlers']['file']['filename'] = LOG_PATH
    logging.config.dictConfig(data)

# We will use specific loggers for different log messages
custom_logger = logging.getLogger('custom')
root_logger = logging.getLogger('root')
flask_logger = logging.getLogger('trashbot')


# Define functions
def scheduler_listener(event):
    '''Listens for execution and crash events and logs the message'''
    if event.exception:
        custom_logger.exception('The job %s (%s) crashed: %s', event.job_id,
                                scheduler.get_job(event.job_id).name,
                                event.exception)
    else:
        custom_logger.info('The job %s (%s) worked', event.job_id,
                           scheduler.get_job(event.job_id).name)


@app.route('/')
def test():
    '''This is a test function to check if the bot is running'''
    custom_logger.debug('Route / test')
    #custom_logger.debug(f'Request headers: \n{request.headers}')
    return 'OK'


@app.route('/callback', methods=['POST'])
def callback():
    '''This is the main function that handles the webhook'''
    custom_logger.debug('Callback accessed')
    #custom_logger.debug('Request headers: \n%s', request.headers)
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    custom_logger.debug('Request body: \n%s', body)
    #request_data = request.get_json()
    #custom_logger.debug('Request: \n%s', request_data['events'][0]['message']['text'])

    # handle webhook body
    try:
        custom_logger.debug('Calling handler')
        handler.handle(body, signature)
    except InvalidSignatureError:
        custom_logger.exception('Invalid signature. \
            Please check your channel access token/channel secret.')
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    '''This function will handle all messages sent to the bot'''
    if event.source.type == 'group':
        if group_info['id'] is None:
            group_info['id'] = event.source.group_id
            custom_logger.debug('Accessing API: get group summary')
            group_summary = line_bot_api.get_group_summary(group_info['id'])
            group_info['name'] = group_summary.group_name

    if event.message.text == '!start':
        scheduler.resume()
        custom_logger.debug(
            f'Accessing API: reply message {event.message.text}')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=COMMANDS['!start']['text']))

    if event.message.text == '!stop':
        scheduler.pause()
        custom_logger.debug(
            f'Accessing API: reply message {event.message.text}')
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=COMMANDS['!stop']['text']))

    if event.message.text == '!help':
        all_commands = ''
        for command, data in COMMANDS.items():
            description = data['description']
            all_commands += f'{command} - {description}\n'
        # Remove the last newline character from the all_commands
        all_commands = all_commands.rstrip('\n')
        help_message = TextSendMessage(text=f'{COMMANDS["!help"]["text"]}\n{all_commands}')
        addon_message = TextSendMessage(text='You can also mention trashbot and duty name')
        custom_logger.debug(
            f'Accessing API: reply message {event.message.text}')
        line_bot_api.reply_message(
            event.reply_token,[help_message, addon_message])
        

    if 'trashbot' in event.message.text.lower():
        for duty_name in DUTIES.keys():
            if duty_name.lower() in event.message.text.lower():
                team_name, team_id, members = roster.check_duty(
                    ROSTER_PATH, duty_name)
                member_names = ', '.join(members)
                duty_frequency = DUTIES[duty_name]
                custom_logger.debug('Accessing API: reply freeform message')
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='Ready to report!'
                        f'\nScheduled {duty_frequency} {duty_name} '
                        f'duty members: {member_names}'))
                break  # Stop iterating once a matching duty is found

    if event.message.text == '!duty':
        for duty_name in DUTIES.keys():
            team_name, team_id, members = roster.check_duty(
                ROSTER_PATH, duty_name)
            member_names = ', '.join(members)
            duty_frequency = DUTIES[duty_name]
            custom_logger.debug(
                f'Accessing API: push message {event.message.text}')
            line_bot_api.push_message(
                group_info['id'],
                TextSendMessage(text=f'Scheduled {duty_frequency} {duty_name} '
                                f'duty members: {member_names}'))


@handler.add(JoinEvent)
def handle_group_joined(event):
    if isinstance(event.source, SourceGroup):
        welcome_message = TextSendMessage(text='Thank you for adding me to this group! I\'m here to assist you with your tasks.')
        help_message = TextSendMessage(text='Try !help to see the list of available commands.')
        messages = [welcome_message, help_message]
        custom_logger.debug('Accessing API: reply message Group join')
        line_bot_api.reply_message(event.reply_token, messages)


def handle_rotation_all_commands(all_commands):
    team_name, team_id, members, duty_name = all_commands
    member_names = ', '.join(members)
    custom_logger.info('Team %s is on %s duty.', team_id, duty_name)
    custom_logger.info('Members: %s', member_names)
    message = TextSendMessage(
        text=f'Good morning dear people of {group_info["name"]}!'
        f'\nTeam {team_id} is on {duty_name} duty.'
        f'\nMembers: {member_names}')
    custom_logger.debug('Accessing API: push message Rotation notification')
    line_bot_api.push_message(group_info['id'], message)


# Add listener to log the execution for debugging purposes
scheduler.add_listener(scheduler_listener,
                       EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Add jobs here and print pending jobs
scheduler.add_job(
    lambda: handle_rotation_all_commands(roster.rotate_duty(ROSTER_PATH, 'Garbage')),
    trigger=CronTrigger(day_of_week='mon', hour=9, timezone='Asia/Tokyo'),
    id='001',
    name='Duty rotation weekly')

scheduler.add_job(lambda: handle_rotation_all_commands(
    roster.rotate_duty(ROSTER_PATH, 'Groceries')),
                  trigger=CronTrigger(day='1st mon',
                                      hour=9,
                                      timezone='Asia/Tokyo'),
                  id='002',
                  name='Duty rotation monthly')

custom_logger.debug(scheduler.get_jobs())

# Configure the scheduler
# After the scheduler has been started, you can no longer alter its settings
scheduler.configure(
    jobstores={'default': {
        'type': 'memory'
    }},
    executors={'default': {
        'type': 'threadpool',
        'max_workers': 10
    }},
    job_defaults={'max_instances': 3})

# Start the scheduler
scheduler.start(paused=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
