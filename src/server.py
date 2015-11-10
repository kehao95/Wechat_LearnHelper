from flask import Flask, request, abort, render_template
import hashlib
import sys
import time

sys.path += ["./lib", "./lib/wechat-python-sdk"]
from wechat_sdk import WechatBasic
from wechat_sdk.messages import (
    TextMessage, VoiceMessage, ImageMessage, VideoMessage, LinkMessage, LocationMessage, EventMessage
)
import logging

_APP_TOKEN = '***REMOVED***'

# logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.debug("Debug Mode On")
logger.info("Info On")

# wechat
wechat = WechatBasic(token=_APP_TOKEN)
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def listener():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    if not wechat.check_signature(signature, timestamp, nonce): abort(500)
    # 测试号绑定
    if request.method == 'GET':
        logger.info("get")
        echostr = request.args.get('echostr')
        return echostr
    else:  # 主要功能
        logger.info("post")
        data = request.get_data().decode('utf-8')
        respose = handle_request(data)
        logger.debug("send response: %s", respose)
        return respose


@app.route('/bind')
def bind_student_account():
    return render_template("bind.html")


def handle_request(data):
    logger.debug("handle_request")
    wechat.parse_data(data)
    message = wechat.get_message()
    openID = message.source
    response = ""
    if isinstance(message, TextMessage):
        print("TextMessage")
        if "绑定" in message.content:
            response = response_bind(openID)
        elif "解除绑定" in message.content:
            return wechat.response_text(content="此功能暂时未开发")
        else:
            return wechat.response_text(content=message.content)
    else:
        print("OtherMessage")
        return wechat.response_text(content="请输入文字信息")
    return response


def response_bind(openID) -> str:
    card = {
        'description': "用户:%s" % openID,
        'picurl': "http://59.66.139.26:5000/bind",
        'url': "http://59.66.139.26:5000/bind",
        'title': "绑定"
    }
    return wechat.response_news([card])


if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=True, use_reloader=False)
