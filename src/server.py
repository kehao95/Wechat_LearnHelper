"""
服务器主程序，用于监听各种事件然后分发处理回复
"""
from flask import Flask, request, abort, render_template, json, jsonify
from datetime import date
from itertools import groupby
import logging
import sys
import json
import time
import requests

sys.path += ["./lib", "./lib/wechat-python-sdk"]
import getip
import db
from timeout import (settimeout, timeout)
from wechat_sdk import WechatBasic
from wechat_sdk.messages import (TextMessage, VoiceMessage, ImageMessage, VideoMessage, LinkMessage, LocationMessage,
                                 EventMessage)

# globals
_MY_IP = ""
_MY_PORT = ""
_HOST_HTTP = ""
_HOST_HTTPS = ""
_APP_TOKEN = ""
_APP_SECRET = ""
_APP_ID = ""
_APP_BUTTONS = ""
_TEMPLATE_SUCCESS = ""
_TEMPLATE_HOMEWORK = ""
_TEMPLATE_ANNOUNCEMENT = ""
_URL_BASE = ""
_URL_LOGIN = ""
app = Flask(__name__)
wechat = None
logger = None

database = None


@app.route('/', methods=['GET', 'POST'])
def main_listener():
    """
    主监听：校验签名、回复绑定请求、其余功能由 handle_request 处理
    :return: response
    """
    # 验证签名
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
        data = request.get_data().decode('utf-8')
        logger.info("post: data: %s" % data)
        handler = Handler(data)
        response = handler.get_response()
        return response


@app.route('/homework')
def show_homework():
    def fit_homework_to_html(homeworkFromDB):
        count = len(homeworkFromDB)
        i = 0
        while i < count:
            (homeworkFromDB[i])["id"] = str(i)
            i += 1
        for hw in homeworkFromDB:
            hw["_Text"] = (hw["_Text"]).replace("\r\n", "</p><p>")
        result = []
        result = [{"endDate": key, "homeworkGroup": list(group)} for key, group in
                  groupby(homeworkFromDB, lambda x: x["_EndTime"])]
        result.sort(key=lambda x: x["endDate"])
        return result

    openID = request.args.get('openID')
    print(openID)
    homeworkFromDB = database.get_works_after_today(openID)
    homeworks = fit_homework_to_html(homeworkFromDB)

    return render_template("homeworklist.html", openID=openID, homeworks=homeworks)


@app.route('/bind', methods=['GET', 'POST'])
def bind_student_account():
    """
    handle user binding event
    for get request (ask for bind) return the binding page
    for post request (user send user name and password)
        check the validation of id&pass
        add to newuser file
        give user success message
    :return:
    """
    def check_vaild(username, password):
        data = dict(
            userid=username,
            userpass=password,
        )
        r = requests.post(_URL_LOGIN, data)
        content = r.content
        if len(content) > 120:
            return False
        else:
            return True

    if request.method == "GET":
        openID = request.args.get('openID')
        return render_template("bind.html", openID=openID)
    if request.method == "POST":
        print("POST")
        logger.debug(request.form)
        openID = request.form["openID"]
        studentID = request.form["studentID"]
        password = request.form["password"]
        result = 0
        if check_vaild(username=studentID, password=password) is not True:
            result = 1
        if result == 0:
            newusers = []
            try:
                newusersdict = json.load(open("newusers.json", 'r'))
            except:
                logger.debug("could not open newusers.json")
            newuser = {
                "username": studentID,
                "openid": openID,
                "password": password
            }
            newusers.append(newuser)
            json.dump(newusers, open("newusers.json", 'w'))
        return jsonify({"result": result})


@app.route('/push', methods=["POST"])
def push_messages():
    """
    if event happens event_loop will send a request to this
    The server will push message to users
    :return:
    """
    data = str(request.get_data(), encoding="utf-8")
    data = json.loads(data)
    push_type = data["type"]
    logger.debug("get push request: %s" % push_type)
    openidlist = map(lambda x: x["openid"], data["users"])
    if push_type == "register_done":
        for user in data['users']:
            send_success_message(user['openid'], user['username'])
    elif push_type == "new_messages":
        send_new_announcement(openidlist, data["data"])
    elif push_type == "new_works":
        send_new_homework(openidlist, data["data"])
    return ""


class Handler:
    """
    消息处理类，对每次微信服务器消息构造一次，各方法共用消息的基本信息
    函数共用user信息使得个性化响应更方便友好
    """
    global wechat
    global logger

    def __init__(self, data):
        self.wechat = wechat
        self.data = data
        wechat.parse_data(data)
        self.message = wechat.message
        self.openID = self.message.source

    def response_bind(self) -> str:
        isalreadybinded = database.isOpenIDBound(self.openID)
        if isalreadybinded:
            return wechat.response_text(content="您已经绑定过学号了。")
        card = {
            'description': "用户:%s" % self.openID,
            'url': "%s/bind?openID=%s" % (_HOST_HTTP, self.openID),
            'title': "绑定"
        }
        return wechat.response_news([card])

    def response_homework(self) -> str:
        isalreadybinded = database.isOpenIDBound(self.openID)
        if not isalreadybinded:
            return wechat.response_text(content="您还未绑定过学号。")
        else:
            card = {
                'description': "用户:%s" % self.openID,
                'url': "%s/homework?openID=%s" % (_HOST_HTTP, self.openID),
                'title': "作业"
            }
            return wechat.response_news([card])

    def response_announce(self) -> str:
        isalreadybinded = database.isOpenIDBound(self.openID)  # functionA(openID)
        if not isalreadybinded:
            return wechat.response_text(content="您还未绑定过学号。")
        announcements = database.get_messages_in_days(self.openID, 30)
        announcements.sort(key=lambda x: x["_Time"], reverse=True)
        cardList = []
        if announcements == []:
            cardNoAnnounce = {
                'description': "用户:%s" % self.openID,
                'url': "",
                'title': "暂无新公告"
            }
            return wechat.response_news(cardNoAnnounce)
        elif len(announcements) < 9:
            cardHead = {
                'description': "",
                'url': "",
                'title': "最新的%d条公告" % len(announcements)
            }
            cardList = [cardHead] + [
                {'title': str(anc["_Time"]) + "|" + anc["_CourseName"] + "\n" + anc["_Title"] + "\n" + anc["_Text"],
                 'url': "", 'description': ""} for anc in announcements]
        else:
            cardHead = {
                'description': "",
                'title': "最新的8条公告"
            }
            cardList = [cardHead] + [
                {'title': str(anc["_Time"]) + "|" + anc["_CourseName"] + "\n" + anc["_Title"] + "\n" + anc["_Text"],
                 'description': ""} for anc in announcements[:8]]

        return wechat.response_news(cardList)

    def get_response(self) -> str:
        """
        根据message类型以及内容确定事件类型
        交给response处理获取并返回response
        :param message data:
        :return: response
        """
        response = ""
        if isinstance(self.message, TextMessage):
            logger.debug("TextMessage")
            content = self.message.content
            if "绑定" in content:
                response = self.response_bind()
            elif "作业" in content:
                response = self.response_homework()
            elif "公告" in content:
                response = self.response_announce()
            elif "解除绑定" in content:
                response = wechat.response_text(content="此功能暂时未开发")
            else:
                response = wechat.response_text(content="Echo:%s" % content)
        elif isinstance(self.message, EventMessage):
            logger.info("EventMessage")
            type = self.message.type
            if type == "click":
                key = self.message.key
                if key == "BIND":
                    response = self.response_bind()
                elif key == "ANNOUNCEMENT":
                    response = self.response_announce()
                elif key == "HOMEWORK":
                    response = self.response_homework()
                elif key == "UNBIND":
                    response = wechat.response_text(content="此功能暂时未开发")
                else:
                    pass
            elif type == "templatesendjobfinish":
                logger.debug("template send job finish")
            else:
                pass
        else:
            return wechat.response_text(content="请输入文字信息")
        return response


def _get_globals():
    # logger
    global logger
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("Debug Mode On")
    logger.info("Info On")
    # get app secrets
    global _APP_ID
    global _APP_SECRET
    global _APP_TOKEN
    global _APP_BUTTONS
    global _TEMPLATE_SUCCESS
    global _TEMPLATE_HOMEWORK
    global _TEMPLATE_ANNOUNCEMENT
    secrets = json.loads(open(".secret.json", "r").read())
    logger.info("load secrets:\n%s" % secrets)
    app = secrets['app']
    _APP_ID = app['appID']
    _APP_TOKEN = app['Token']
    _APP_SECRET = app['appsecret']
    _APP_BUTTONS = app['buttons']
    _TEMPLATE_SUCCESS = app['successTemplate']
    _TEMPLATE_HOMEWORK = app['homeworkTemplate']
    _TEMPLATE_ANNOUNCEMENT = app['announcementTemplate']
    # get ip
    global _MY_IP
    global _MY_PORT
    global _HOST_HTTP
    global _HOST_HTTPS
    _MY_IP = getip.myip()
    _MY_PORT = secrets["server"]["port"]
    _HOST_HTTP = "http://%s:%s" % (_MY_IP, _MY_PORT)
    _HOST_HTTPS = "https://%s:%s" % (_MY_IP, _MY_PORT)
    logger.info("local address:%s" % _HOST_HTTP)
    with open("address.txt", 'w') as f:
        f.write(_HOST_HTTP + "/push")
    # thu learn urls
    global _URL_BASE
    global _URL_LOGIN
    _URL_BASE = 'https://learn.tsinghua.edu.cn'
    _URL_LOGIN = _URL_BASE + '/MultiLanguage/lesson/teacher/loginteacher.jsp'

    # wechat
    global wechat
    wechat = WechatBasic(token=_APP_TOKEN, appid=_APP_ID, appsecret=_APP_SECRET)
    # database
    global database
    db_secret = secrets['database']
    database = db.Database(username=db_secret['username'], password=db_secret['password'],
                           database=db_secret['database_name'], salt=db_secret['key'], address=db_secret['host'])


def _create_buttons():
    # delete
    respond = wechat.delete_menu()
    logger.info("Delete Button: %s" % respond)
    # add
    respond = wechat.create_menu(_APP_BUTTONS)
    logger.debug("Add Button: %s" % respond)


def send_success_message(openID, studentnumber):
    pushdata = {
        "studentnumber": {
            "value": studentnumber,
            "color": "#ff0000"
        }
    }
    wechat.send_template_message(user_id=openID, template_id=_TEMPLATE_SUCCESS, data=pushdata, url="")


def send_new_homework(openIDs, homework):
    pushdata = {
        "coursename": {
            "value": homework["course_name"],
            "color": "#228B22"
        },
        "title": {
            "value": homework["title"],
            "color": "#228B22"
        },
        "endtime": {
            "value": str(homework["end_time"]),
            "color": "#228B22"
        },
        "text": {
            "value": homework["detail"],
            "color": "#228B22"
        }
    }
    for user_id in openIDs:
        wechat.send_template_message(user_id=user_id, template_id=_TEMPLATE_HOMEWORK, data=pushdata, url="")


def send_new_announcement(openIDs, annoucement):
    pushdata = {
        "coursename": {
            "value": annoucement["course_name"],
            "color": "#0000ff"
        },
        "title": {
            "value": annoucement["title"],
            "color": "#0000ff"
        },
        "time": {
            "value": str(annoucement["date"]),
            "color": "#0000ff"
        },
        "text": {
            "value": annoucement["detail"],
            "color": "#0000ff"
        }
    }
    for user_id in openIDs:
        wechat.send_template_message(user_id=user_id, template_id=_TEMPLATE_ANNOUNCEMENT, data=pushdata, url="")


def main():
    _get_globals()
    try:
        _create_buttons()
    except:
        pass
    app.run(host='0.0.0.0', use_debugger=True, use_reloader=False, port=_MY_PORT)


if __name__ == '__main__':
    main()
