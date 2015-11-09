from flask import Flask, request, abort, render_template
import hashlib
import sys

try:
    sys.path+=[".\\lib",".\\lib\\wechat-python-sdk"]
except:
    sys.path+=["./lib","./lib/wechat-python-sdk"]
from wechat_sdk import WechatBasic
from wechat_sdk.messages import (
    TextMessage, VoiceMessage, ImageMessage, VideoMessage, LinkMessage, LocationMessage, EventMessage
)
import logging

_APP_TOKEN = '***REMOVED***'
#requestCases = {'绑定': respBind,}

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
    wechat
    if check_SHA1(request) is False: abort(500)
    # 测试号绑定
    if request.method == 'GET':
        logger.info("get")
        echostr = request.args.get('echostr')
        return echostr
    else:  # 主要功能
        logger.info("post")
        respose = handle_request(request)
        logger.debug("send response: %s",respose)
        return respose


def check_SHA1(request):
    try:
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        token = _APP_TOKEN
        print(signature)
        l = [token, timestamp, nonce]
        l.sort()
        sha1 = hashlib.sha1()
        sha1.update("".join(l).encode('utf-8'))
        hashcode = sha1.hexdigest()
        if hashcode == signature:
            logger.info("Sha1 check valid")
            return True
        else:
            return False
    except(Exception):
        logger.error("invalid URL")
        return False


def respBind(customerID):
    return "http://59.66.139.196:5000/bind"


def handle_request(request):
    logger.debug("handle_request")
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    data = request.get_data().decode('utf-8')
    wechat.parse_data(data)
    message = wechat.get_message()
    customerID = message.source
    response = ""

    if isinstance(message, TextMessage):
        print("TextMessage")
        respCont = ""
        try:
            respCont = requestCases.get(message.content)(customerID)
        except:
            respCont = "指令无效"

        response = wechat.response_text(content=respCont)
    else:
        print("OtherMessage")
        response = wechat.response_text(content="请输入文字信息")
    return response




@app.route('/bind')
def bindStAccount():
    return render_template("bind.html")

requestCases = {"绑定": respBind}


if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=True, use_reloader=False)
