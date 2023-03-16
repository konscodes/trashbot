from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from logging.config import dictConfig
import json

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

with open(BASE_DIR + '/trashbot/logging_conf.json', 'r') as json_data:
    data = json.load(json_data)

dictConfig(data)

app = Flask(__name__)

line_bot_api = LineBotApi(str(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')))
handler = WebhookHandler(str(os.environ.get('LINE_CHANNEL_SECRET')))

@app.route("/")
def test():
    app.logger.info(request.headers)
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    app.logger.info(request.headers)
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.exception("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()