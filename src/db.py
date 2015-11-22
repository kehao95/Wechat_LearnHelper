#!/usr/bin/python
# -*- coding: UTF-8 -*

from __future__ import print_function
from decimal import Decimal
from datetime import datetime, date, timedelta
import mysql.connector

class Database:
    S_GET_DATA_BY_OPENID = "SELECT UID,UPd FROM UserInfo WHERE OpenID = %s"
    S_GET_DATA_BY_UID = "SELECT UID,UPd FROM UserInfo WHERE UID = %s"
    S_GET_CID_BY_UID = "SELECT CID FROM UserCourse WHERE UID = %s"
    S_GET_MSG_BY_CID = "SELECT CID,Time,Title,Text FROM Message WHERE CID = %s"
    S_GET_MSG_IN_DAYS = "SELECT CID,Time,Title,Text FROM Message WHERE CID = %s AND DATE_SUB(CURDATE(),INTERVAL %s DAY) <= date(Time)"
    # S_GET_WORK_BY_CID = "SELECT CID,EndTime,Title,Text WHERE CID = %s"
    S_GET_COURSENAME = "SELECT CID,Name FROM CourseName"
    S_GET_WORK_AFTER = "SELECT CID,EndTime,Title,WID,Text FROM Work WHERE CID = %s AND EndTime > DATE(%s)"

    S_IS_WORK_FINISHED = "SELECT HID FROM WorkFinished WHERE UID = %s AND HID = %s"

    S_INSERT_WORKFINISHED = "INSERT IGNORE INTO WorkFinished (UID,HID) VALUES(%s,%s)"
    S_INSERT_USERINFO = "INSERT IGNORE INTO UserInfo (UID,UPd,OpenID) VALUES (%s,%s,%s)"
    S_INSERT_WORK = "INSERT IGNORE INTO Work (WID, CID, EndTime, Title, Text) VALUES (%s,%s,DATE(%s),%s,%s)"
    S_INSERT_COURSENAME = "INSERT IGNORE INTO CourseName (CID, Name) VALUES(%s,%s)"
    S_INSERT_MESSAGE = "INSERT IGNORE INTO Message (MID,CID,Time,Title,Text) VALUES(%s,%s,DATE(%s),%s,%s)"
    S_INSERT_USERCOURSE = "INSERT IGNORE INTO UserCourse (UID,CID) VALUES(%s,%s)"

    S_DATABASE_NAME = 'wechat_learnhelper'
    cnx = None
    courseNameDict = {}

    def __init__(self, username, password):
        self.cnx = mysql.connector.connect(user=username, database= self.S_DATABASE_NAME, host='127.0.0.1', password=password)
        self.courseNameLoad()
        
        


    def build_database(self):
        S_SET_UTF8 = "alter database %s character set utf8 collate utf8_unicode_ci"

        S_BUILD_COURSENAME = "create table CourseName (CID int primary key, Name varchar(30))"
        S_BUILD_WORK = "create table Work (WID int primary key, CID int, EndTime date, Text varchar(32767), Title varchar(63))"
        S_BUILD_MESSAGE = "create table Message (MID int primary key, CID int, Time date, Sender varchar(14), Text varchar(32767), Title varchar(63))"
        S_BUILD_USERINFO = "create table UserInfo (UID int primary key, UPd varchar(25), OpenID varchar(30))"
        S_BUILD_USERCOURSE = "create table UserCourse (UID int, CID int, primary key(UID, CID))"
        S_BUILD_WORKFINISHED = "create table WorkFinished (UID int, HID int, primary key(UID, HID))"

        cur = self.cnx.cursor(buffered=True)
        cur.execute(self.S_BUILD_COURSENAME)
        cur.execute(self.S_BUILD_MESSAGE)
        cur.execute(self.S_BUILD_WORK)
        cur.execute(self.S_BUILD_USERINFO)
        cur.execute(self.S_BUILD_USERCOURSE)
        cur.execute(self.S_BUILD_WORKFINISHED)
        cur.execute(self.S_SET_UTF8, (self.S_DATABASE_NAME,))


    #build_database()

    def get_data_from_openid(self, openID):
        cur = self.cnx.cursor(buffered=True)
        cur.execute(self.S_GET_DATA_BY_OPENID, (openID,))
        for i in cur:
            return i


    def isOpenIDBound(self, openID):
        return self.get_data_from_openid(openID) != None


    def courseNameLoad(self):
        cur = self.cnx.cursor(buffered=True)
        cur.execute(self.S_GET_COURSENAME)
        for cid, name in cur:
            self.courseNameDict[cid] = name


    def bind_user_openID(self, uid, upd, openID):
        cur = self.cnx.cursor(buffered=True)
        cur.execute(self.S_GET_DATA_BY_UID, (uid,))
        if (cur.rowcount != 0):
            return 2
        cur.execute(self.S_INSERT_USERINFO, (uid, upd, openID))
        self.cnx.commit()
        return 1 - cur.rowcount  # 0:success  1:failure


    def store(self, d):
        cur = self.cnx.cursor(buffered=True)
        uid = int(d['_user']['username'])
        cur.execute(self.S_GET_DATA_BY_OPENID, (d['_user']['openID'],))
        for course in d['_courses']:
            cid = course['_id']
            cur.execute(self.S_INSERT_USERCOURSE, (uid, cid))
            cur.execute(self.S_INSERT_COURSENAME, (cid, course['_name']))
            for work in course['_works']:
                cur.execute(self.S_INSERT_WORK, (work['_id'], cid, work['_end_time'], work['_title'], work['_details']))
                if work['_submitted'] == True:
                    cur.execute(self.S_INSERT_WORKFINISHED, (uid, work['_id']))
            for msg in course['_messages']:
                cur.execute(self.S_INSERT_MESSAGE, (msg['_id'], cid, msg['_date'], msg['_title'], msg['_details']))
        self.cnx.commit()
        courseNameLoad()

    def get_all_messages(self, openID):
        ret = []
        uid, upd = self.get_data_from_openid(openID)
        curC = self.cnx.cursor(buffered=True)
        curM = self.cnx.cursor(buffered=True)
        curC.execute(self.S_GET_CID_BY_UID, (uid,))
        for course in curC:
            if (course[0] == 126501):
                continue
            curM.execute(self.S_GET_MSG_BY_CID, (course[0],))
            for msg in curM:
                # CID,Time,Title,Text
                elem = {'_Time': msg[1], '_Title': msg[2], '_CourseName': self.courseNameDict[msg[0]]}
                ret.append(elem)
        return ret

    def get_messages_in_days(self, openID, days):
        ret = []
        uid, upd = self.get_data_from_openid(openID)
        curC = self.cnx.cursor(buffered=True)
        curM = self.cnx.cursor(buffered=True)
        curC.execute(self.S_GET_CID_BY_UID, (uid,))
        for course in curC:
            if (course[0] == 126501):
                continue
            curM.execute(self.S_GET_MSG_IN_DAYS, (course[0], days))
            for msg in curM:
                # CID,Time,Title,Text
                elem = {'_Time': msg[1], '_Title': msg[2], '_CourseName': self.courseNameDict[msg[0]], '_Text': msg[3]}
                ret.append(elem)
        return ret


    def is_work_finished(self, uid, hid):
        cur = self.cnx.cursor(buffered=True)
        cur.execute(self.S_IS_WORK_FINISHED,(uid, hid))
        if cur.rowcount == 0:
            return False
        else:
            return True


    def get_works_after_today(self, openID):
        ret = []
        uid, upd = self.get_data_from_openid(openID)
        curC = self.cnx.cursor(buffered=True)
        curW = self.cnx.cursor(buffered=True)
        curC.execute(self.S_GET_CID_BY_UID, (uid,))
        for course in curC:
            curW.execute(self.S_GET_WORK_AFTER, (course[0], date.today()))
            for work in curW:
                # print(work)
                # CID,EndTime,Title,WID,Text
                elem = {'_EndTime': work[1], '_CourseName': self.courseNameDict[work[0]], '_Title': work[2],
                        '_Finished': self.is_work_finished(uid, work[3]), '_Text': work[4]}
                ret.append(elem)
        return ret

