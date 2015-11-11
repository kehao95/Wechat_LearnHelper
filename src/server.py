from flask import Flask, request, abort, render_template, json, jsonify
from datetime import date
from itertools import groupby
import hashlib
import sys
import time

from learn_spider import *
import database

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
    openID = request.args.get('openID')
    print(openID)
    return render_template("bind.html", openID=openID)


@app.route('/homework')
def show_homework():
    openID = request.args.get('openID')
    print(openID)
    homeworkFromDB = database.get_works_after_today(openID)
#    homeworkFromDB = [
#        {"_EndTime":date(1999,5,4),"_CourseName":"软件工程", "_Title":"迭代一", "_Finished": True},
#        {"_EndTime":date(1999,5,4),"_CourseName":"操作系统", "_Title":"迭代N", "_Finished": True},
#        {"_EndTime":date(1998,5,4),"_CourseName":"计算机", "_Title":"Chap2", "_Finished": False},
#        {"_EndTime":date(1999,5,14),"_CourseName":"Haskell", "_Title":"第六次", "_Finished": True},
#        {"_EndTime":date(1999,6,4),"_CourseName":"软件工程", "_Title":"迭代233", "_Finished": False},
#    ]  #functionA(openID)
    homeworks = fit_homework_to_html(homeworkFromDB)

    return render_template("homeworklist.html", openID=openID, homeworks=homeworks)


def bind_uid_openid(openID, studentID, password):
    if not thu_learn.login(studentID,password):
        return 1
    return database.bind_user_openID(studentID,password,openID)

@app.route('/bindID', methods=['GET', 'POST'])
def bind_st_account():
    if request.method == "POST":
        print("POST")
        print(request.form)

    openID = request.form["openID"]
    studentID = request.form["studentID"]
    password = request.form["password"]

#    print(openID)
#    print(studentID)
#    print(password)
    result = bind_uid_openid(openID,studentID,password)#functionA(openID, studentID, password)
    if result == 0:
        spider = Spider(openID,studentID, password)
        database.store(spider.get_dict())
    print("_____CHECKPOINT_______")
    print("_____CHECKPOINT_______")
    return jsonify({"result": result})

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
        elif "作业" in message.content:
            response = response_homework(openID)
        elif "公告" in message.content:
            response = response_announce(openID)
        elif "解除绑定" in message.content:
            return wechat.response_text(content="此功能暂时未开发")
        else:
            return wechat.response_text(content=message.content)
    else:
        print("OtherMessage")
        return wechat.response_text(content="请输入文字信息")
    return response


def response_bind(openID) -> str:
    isalreadybinded = database.isOpenIDBound(openID)
    #isalreadybinded = False  #functionA(openID)

    if isalreadybinded:
        return wechat.response_text(content="您已经绑定过学号了。")
    else:
        card = {
            'description': "用户:%s" % openID,
            'picurl': "http://59.66.139.97:5000/bind?openID=%s"%openID,
            'url': "http://59.66.139.97:5000/bind?openID=%s"%openID,
            'title': "绑定"
        }
        return wechat.response_news([card])


def response_homework(openID) -> str:
    isalreadybinded = database.isOpenIDBound(openID)  #functionA(openID)
    if not isalreadybinded:
        return wechat.response_text(content="您还未绑定过学号。")
    else:
        card = {
            'description': "用户:%s" % openID,
            #'picurl': "http://59.66.139.196:5000/homework?openID=%s"%openID,
            'url': "http://59.66.139.97:5000/homework?openID=%s"%openID,
            'title': "作业"
        }
        return wechat.response_news([card])


def response_announce(openID) -> str:
    isalreadybinded = database.isOpenIDBound(openID)  #functionA(openID)
    if not isalreadybinded:
        return wechat.response_text(content="您还未绑定过学号。")
    else:
        print(openID)
        #openID="3"
        announcements = database.get_messages_in_days(openID,30)
        """
        announcements = [

#            {"_Time":date(2011,1,1),"_CourseName":"软件工程","_Title":"请同学们迭代一注意控制时间"},
#            {"_Time":date(2011,1,2),"_CourseName":"软件工程","_Title":"邮箱","_Text"},
#            {"_Time":date(2011,1,1),"_CourseName":"工图","_Title":"大作业要求"},
#            {"_Time":date(2011,1,15),"_CourseName":"计网","_Title":"大作业要求"},
#            {"_Time":date(2010,1,1),"_CourseName":"计网","_Title":"大作业要求"},
#            {"_Time":date(2011,1,31),"_CourseName":"函数式语言","_Title":"大作业要求"},
#            {"_Time":date(2011,12,1),"_CourseName":"操作系统","_Title":"大作业要求"},
#            {"_Time":date(2011,1,11),"_CourseName":"操作系统","_Title":"代码报告要求"},
#            {"_Time":date(2011,1,31),"_CourseName":"操作系统","_Title":"作业已上传"},
#            {"_Time":date(2011,12,1),"_CourseName":"操作系统","_Title":"大作业要求"},
#            {"_Time":date(2011,1,11),"_CourseName":"操作系统","_Title":"代码报告要求"},
#            {"_Time":date(2011,1,31),"_CourseName":"操作系统","_Title":"作业已上传"},
        ]
        """
        announcements.sort(key=lambda x:x["_Time"])
        announcements.reverse()
        cardList = []
        if announcements == []:
            cardNoAnnounce = {
                'description': "用户:%s" % openID,
                'url': "",
                'title': "暂无新公告"
            }
            return wechat.response_news(cardNoAnnounce)
        elif len(announcements) < 9:
            cardHead = {
                'description': "",
                'url': "",
                'title': "最新的%d条公告"%len(announcements)
            }
            cardList = [cardHead] + [{ 'title': str(anc["_Time"])+"|"+anc["_CourseName"]+"\n"+anc["_Title"]+"\n"+anc["_Text"], 'url': "", 'description': "" } for anc in announcements]
        else:
            cardHead = {
                'description': "",
                'url': "",
                'title': "最新的8条公告"
            }
            cardList = [cardHead] + [{ 'title': str(anc["_Time"])+"|"+anc["_CourseName"]+"\n"+anc["_Title"]+"\n"+anc["_Text"], 'url': "", 'description': "" } for anc in announcements[:8]]

        return wechat.response_news(cardList)


def fit_homework_to_html(homeworkFromDB):
    result = []
    result = [{"endDate":key, "homeworkGroup":list(group)} for key,group in groupby(homeworkFromDB,lambda x:x["_EndTime"])]
    result.sort(key=lambda x:x["endDate"])
    return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=True, use_reloader=False)


