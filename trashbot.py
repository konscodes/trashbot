from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from os.path import dirname, abspath
from os import environ
import logging
import logging.config
from flask import Flask, request, abort
import json

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = dirname(abspath(__file__))
LOG_PATH = BASE_DIR + '/logs/logger.log'

# Read JSON and configure logging using dictionary
with open(BASE_DIR + '/logging_conf.json', 'r') as f:
    data = json.load(f)
    data["handlers"]["file"]["filename"] = LOG_PATH
    logging.config.dictConfig(data)

app = Flask(__name__)

# We will use specific loggers for different log messages
custom_logger = logging.getLogger('custom')
root_logger = logging.getLogger('root')
flask_logger = logging.getLogger('trashbot')

# Line API requires a token for access and handler needs secret
line_bot_api = LineBotApi(str(environ.get('LINE_CHANNEL_ACCESS_TOKEN')))
handler = WebhookHandler(str(environ.get('LINE_CHANNEL_SECRET')))

@app.route("/")
def test():
    custom_logger.info(f"Request headers: \n{request.headers}")
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    custom_logger.info(f"Request headers: \n{request.headers}")
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    custom_logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        custom_logger.exception("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# Main bot function
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    app.run()
