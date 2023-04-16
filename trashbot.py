'''This bot will send a reoccurring reminders on garbage collection schedule'''
import json
import logging
import logging.config
import os

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = BASE_DIR + '/logs/logger.log'

# Read JSON and configure logging using dictionary
with open(BASE_DIR + '/logging_conf.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    data['handlers']['file']['filename'] = LOG_PATH
    logging.config.dictConfig(data)

# Create a new Flask instance
app = Flask(__name__)

# Create a new Scheduler instance
scheduler = BackgroundScheduler()

# Scheduler configuration
jobstores = {'default': {'type': 'memory'}}
executors = {'default': {'type': 'threadpool', 'max_workers': 10}}
job_defaults = {'max_instances': 3}

# We will use specific loggers for different log messages
custom_logger = logging.getLogger('custom')
root_logger = logging.getLogger('root')
flask_logger = logging.getLogger('trashbot')

# Line API requires a token for access and handler needs secret
line_bot_api = LineBotApi(str(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')))
handler = WebhookHandler(str(os.environ.get('LINE_CHANNEL_SECRET')))
custom_logger.debug('Line token: %s',
                    str(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')))
custom_logger.debug('Line secret: %s',
                    str(os.environ.get('LINE_CHANNEL_SECRET')))


def scheduler_listener(event):
    '''Listens for execution and crash events and logs the message'''
    if event.exception:
        custom_logger.exception('The job crashed %s', event.exception)
    else:
        custom_logger.info('The job worked')


@app.route('/')
def test():
    '''This is a test function to check if the bot is running'''
    custom_logger.debug('Route / test')
    #custom_logger.debug(f'Request headers: \n{request.headers}')
    return 'OK'


@app.route('/callback', methods=['POST'])
def callback():
    '''This is the main function that handles the webhook'''
    custom_logger.debug('Request headers: \n%s', request.headers)
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    custom_logger.debug('Request body: \n%s', body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        custom_logger.exception('Invalid signature. \
            Please check your channel access token/channel secret.')
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    '''This function will handle all messages sent to the bot'''
    line_bot_api.reply_message(event.reply_token,
                               TextSendMessage(text=event.message.text))


# Define function to send message
def send_message(group_id, message):
    # Send the message to the group
    line_bot_api.push_message(group_id, message)


if __name__ == '__main__':
    # Add listener to log the execution for debugging purposes
    scheduler.add_listener(scheduler_listener,
                           EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Set up message to be sent
    message = TextSendMessage(text='Hello, this is a weekly reminder!')

    # Add jobs here and print pending jobs
    scheduler.add_job(
        lambda: send_message('Cd8838ffe33ac87f0595ac2be8ce6579f', message),
        trigger='interval',
        seconds=30,
        timezone='Asia/Tokyo',
        id='001',
        name='Duty reminder')
    custom_logger.debug(scheduler.get_jobs())

    # Configure the scheduler
    # After the scheduler has been started, you can no longer alter its settings
    scheduler.configure(jobstores=jobstores,
                        executors=executors,
                        job_defaults=job_defaults)

    # Start the scheduler
    scheduler.start()

    try:
        # This is here to simulate application activity (keeps the main thread alive)
        app.run(host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        # Handle keyboard interrupts or system exits by shutting down the scheduler
        print('\nShutting down')
        scheduler.shutdown()
