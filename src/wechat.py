from flask import Flask, request, abort
import hashlib
import xmltodict
import time

app = Flask(__name__)

_APP_TOKEN = '***REMOVED***'




@app.route('/', methods=['GET', 'POST'])
def listener():
    if check_SHA1(request) is False: abort(500)
    if request.method == 'GET':
        print("GET")
        echostr = request.args.get('echostr')
        return echostr
    else:  # "POST"
        print("POST")
        data = xmltodict.parse(request.data)
        MessageType = data['xml']['MsgType']
        if MessageType == 'text':
            print("MessageType text")
            Content = data['xml']['Content']
            if "作业" in Content:
                return response_pack(data, demo("作业"))
            elif "通知" in Content:
                return response_pack(data, demo("通知"))
            print("请输入“作业”或“通知”进行测试")
            response = response_pack(data,"请输入“作业”或“通知”进行测试")
            return response
        else:
            return ""

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


def response_pack(data, re_string=None):
    xml = data['xml']
    xml['CreateTime'] = str(int(time.time()))
    xml['FromUserName'], xml['ToUserName'] = xml['ToUserName'], xml['FromUserName']
    if re_string is not None:
        xml['Content'] = re_string
    response = xmltodict.unparse(data)
    return response

def demo(demo_type):
    if demo_type=="作业":
        print("作业")
        with open('/home/kehao/Repo/Wechat_LearnHelper/demo_deadlines', 'r') as f:
            r = "".join(f.readlines())
            r+="底部为最近需提交的作业"
            print(r)
            return r
    elif demo_type=="通知":
        print("通知")
        with open('/home/kehao/Repo/Wechat_LearnHelper/demo_messages', 'r') as f:
            r = "".join(f.readlines())
            r+="底部的为最新通知"
            print(r)
            return r




if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=True, use_reloader=False)



