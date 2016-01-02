"""
消息处理类
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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Handler:
    """
    消息处理类，对每次微信服务器消息构造一次，各方法共用消息的基本信息
    函数共用user信息使得个性化响应更方便友好
    """
    global wechat
    global logger

    def __init__(self, data, database, _HOST_HTTP):
        self.wechat = wechat
        self.data = data
        wechat.parse_data(data)
        self.message = wechat.message
        self.openID = self.message.source

        self.database = database
        self._HOST_HTTP = _HOST_HTTP

        self.KEYS_NEED_BIND = set("ANNOUNCEMENT", "ANNOUNCEMENT_COURSE", "HOMEWORK")


    def response_bind(self) -> str:
        userstatus = self.database.get_status_by_openid(self.openID)
        if userstatus == self.database.STATUS_WAITING or userstatus == self.database.STATUS_OK:
            return wechat.response_text(content="您已经绑定过学号。")
        elif userstatus == self.database.STATUS_NOT_FOUND or userstatus == self.database.STATUS_DELETE:
            pass
        card = {
            'description': "点击进入绑定页面",
            'url': "%s/bind?openID=%s" % (self._HOST_HTTP, self.openID),
            'title': "绑定"
        }
        return wechat.response_news([card])

    def response_unbind(self) -> str:
        userstatus = self.database.get_status_by_openid(self.openID)
        if userstatus == self.database.STATUS_NOT_FOUND or userstatus == self.database.STATUS_DELETE:
            return wechat.response_text(content="您还未绑定过学号。")
        elif userstatus == self.database.STATUS_WAITING or userstatus == self.database.STATUS_OK:
            self.database.unbind_user_openID(self.openID)
            return wechat.response_text(content="您已成功解除绑定。")

    def response_homework(self) -> str:
        card = {
            'description': "点击查看所有未截止作业",
            'url': "%s/homework?openID=%s" % (self._HOST_HTTP, self.openID),
            'title': "作业"
        }
        return wechat.response_news([card])

    def response_announcement_course(self) -> str:
        card = {
            'description': "",
            'url': "%s/announcement_course/%s" % (self._HOST_HTTP, self.openID),
            'title': "点击选择课程"
        }
        return wechat.response_news([card])

    def response_announcement(self) -> str:
        announcements = self.database.get_messages_in_days(self.openID, 10)
        announcements.sort(key=lambda x: x["_Time"], reverse=True)
        cardList = []
        if announcements == []:
            cardNoAnnounce = {
                'description': "用户:%s" % self.openID,
                'url': "",
                'title': "暂无新公告"
            }
            return wechat.response_news([cardNoAnnounce])
        elif len(announcements) < 9:
            cardHead = {
                'description': "",
                'url': "",
                'title': "最新的%d条公告" % len(announcements)
            }
            cardList = [cardHead] + [
                {'title': str(anc["_Time"]) + "|" + anc["_CourseName"] + "\n" + anc["_Title"],
                 'url': "%s/announcement/%s" % (self._HOST_HTTP, anc["_ID"]), 'description': ""} for anc in announcements]
        else:
            cardHead = {
                'description': "",
                'url': "%s/showAllAnc/%s" % (self._HOST_HTTP, self.openID),
                'title': "点击查看更多公告"
            }
            cardList = [cardHead] + [
                {'title': str(anc["_Time"]) + "|" + anc["_CourseName"] + "\n" + anc["_Title"],
                 'url': "%s/announcement/%s" % (self._HOST_HTTP, anc["_ID"]), 'description': ""} for anc in announcements[:6]]

        return wechat.response_news(cardList)

    @settimeout(3)
    def get_response(self) -> str:
        """
        根据message类型以及内容确定事件类型
        交给response处理获取并返回response
        :param message data:
        :return: response
        """
        response = ""
        if isinstance(self.message, EventMessage):
            logger.info("EventMessage")
            type = self.message.type
            if type == "click":
                key = self.message.key
                if key in self.KEYS_NEED_BIND:
                    userstatus = self.database.get_status_by_openid(self.openID)
                    if userstatus == self.database.STATUS_NOT_FOUND or userstatus == self.database.STATUS_DELETE:
                        return wechat.response_text(content="您还未绑定过学号")
                    elif userstatus == self.database.STATUS_WAITING:
                        return wechat.response_text(content="正在为您开启服务，此过程不会超过一分钟，请在收到提示后查询")
                    elif userstatus == self.database.STATUS_OK:
                        pass

                    if key == "ANNOUNCEMENT":
                        response = self.response_announcement()
                    elif key == "ANNOUNCEMENT_COURSE":
                        response = self.response_announcement_course()
                    elif key == "HOMEWORK":
                        response = self.response_homework()
                elif key == "BIND":
                    response = self.response_bind()
                elif key == "UNBIND":
                    response = self.response_unbind()
                else:
                    pass
            elif type == "templatesendjobfinish":
                logger.debug("template send job finish")
            else:
                pass
        else:
            return wechat.response_text(content="请点击功能按钮")
        return response