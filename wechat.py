from flask import Flask, request, abort
import hashlib
import xmltodict
import time

app = Flask(__name__)

_APP_TOKEN = '***REMOVED***'


def check_SHA1(request):
    try:
        echostr = request.args.get('echostr')
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        token = _APP_TOKEN
        l = [token, timestamp, nonce]
        l.sort()
        sha1 = hashlib.sha1()
        sha1.update("".join(l).encode('utf-8'))
        hashcode = sha1.hexdigest()
        if hashcode == signature:
            print("SHA1 check vaild")
            return True
        else:
            return False
    except(Exception):
        print("invaild url")
        return False


def handle_text(data):
    print('text')
    data['xml']['CreateTime'] = str(int(time.time()))
    data['xml']['FromUserName'], data['xml']['ToUserName'] = data['xml']['ToUserName'], data['xml'][
        'FromUserName']
    data = xmltodict.unparse(data)
    return data


def handle_image(data):
    print("image")
    return ""


def handle_data(MessageType, data):
    functions = {
        "text": handle_text,
        "image": handle_image,
    }
    try:
        functions[MessageType](data)
    except(Exception):
        print("MessageType : %s" % MessageType)
        return ""


@app.route('/', methods=['GET', 'POST'])
def listener():
    print("route '/'")
    # if check_SHA1(request) is False: return "invalid"
    if request.method == 'GET':
        print("GET")
        echostr = request.args.get('echostr')
        return echostr
    else:  # "POST"
        print("POST")
        data = xmltodict.parse(request.data)
        MessageType = data['xml']['MsgType']
        handle_data(MessageType, data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=False, use_reloader=False)
