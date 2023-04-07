'''This bot will send a reoccurring reminders on garbage collection schedule'''
from os.path import dirname, abspath
from os import environ
import json
import logging
import logging.config
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask import Flask, request, abort


# Build paths inside the project
BASE_DIR = dirname(abspath(__file__))
LOG_PATH = BASE_DIR + '/logs/logger.log'

# Read JSON and configure logging using dictionary
with open(BASE_DIR + '/logging_conf.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    data['handlers']['file']['filename'] = LOG_PATH
    logging.config.dictConfig(data)

app = Flask(__name__)

# We will use specific loggers for different log messages
custom_logger = logging.getLogger('custom')
root_logger = logging.getLogger('root')
flask_logger = logging.getLogger('trashbot')

# Line API requires a token for access and handler needs secret
line_bot_api = LineBotApi(str(environ.get('LINE_CHANNEL_ACCESS_TOKEN')))
handler = WebhookHandler(str(environ.get('LINE_CHANNEL_SECRET')))

@app.route('/')
def test():
    '''This is a test function to check if the bot is running'''
    custom_logger.debug('This is a test')
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

# Main bot function
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    '''This function will handle all messages sent to the bot'''
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

if __name__ == '__main__':
    app.run()
