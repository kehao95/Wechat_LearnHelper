#!/usr/bin/python
# -*- coding: UTF-8 -*

from __future__ import print_function
from decimal import Decimal
from datetime import datetime, date, timedelta
import mysql.connector

s_database_name = 'wechat_learnhelper'
cnx = mysql.connector.connect(user='root', database=s_database_name, host='127.0.0.1', password="123456")

courseNameDict = {}


def build_database():
    s_set_utf8 = "alter database %s character set utf8 collate utf8_unicode_ci"

    s_build_CourseName = "create table CourseName (CID int primary key, Name varchar(30))"
    s_build_Work = "create table Work (WID int primary key, CID int, EndTime date, Text varchar(32767), Title varchar(63))"
    s_build_Message = "create table Message (MID int primary key, CID int, Time date, Sender varchar(14), Text varchar(32767), Title varchar(63))"
    s_build_UserInfo = "create table UserInfo (UID int primary key, UPd varchar(25), OpenID varchar(30))"
    s_build_UserCourse = "create table UserCourse (UID int, CID int, primary key(UID, CID))"
    s_build_WorkFinished = "create table WorkFinished (UID int, HID int, primary key(UID, HID))"

    cur = cnx.cursor(buffered=True)
    cur.execute(s_build_CourseName)
    cur.execute(s_build_Message)
    cur.execute(s_build_Work)
    cur.execute(s_build_UserInfo)
    cur.execute(s_build_UserCourse)
    cur.execute(s_build_WorkFinished)
    cur.execute(s_set_utf8, (s_database_name,))


build_database()

s_get_data_by_openid = "SELECT UID,UPd FROM UserInfo WHERE OpenID = %s"
s_get_data_by_uid = "SELECT UID,UPd FROM UserInfo WHERE UID = %s"
s_get_cid_by_uid = "SELECT CID FROM UserCourse WHERE UID = %s"
s_get_msg_by_cid = "SELECT CID,Time,Title,Text FROM Message WHERE CID = %s"
s_get_msg_in_days = "SELECT CID,Time,Title,Text FROM Message WHERE CID = %s AND DATE_SUB(CURDATE(),INTERVAL %s DAY) <= date(Time)"
# s_get_work_by_cid = "SELECT CID,EndTime,Title,Text WHERE CID = %s"
s_get_courseName = "SELECT CID,Name FROM CourseName"
s_get_work_after = "SELECT CID,EndTime,Title,WID FROM Work WHERE CID = %s AND EndTime > DATE(%s)"

s_is_work_finished = "SELECT HID FROM WorkFinished WHERE UID = %s AND HID = %s"

s_insert_WorkFinished = "INSERT IGNORE INTO WorkFinished (UID,HID) VALUES(%s,%s)"
s_insert_UserInfo = "INSERT IGNORE INTO UserInfo (UID,UPd,OpenID) VALUES (%s,%s,%s)"
s_insert_Work = "INSERT IGNORE INTO Work (WID, CID, EndTime, Title, Text) VALUES (%s,%s,DATE(%s),%s,%s)"
s_insert_CourseName = "INSERT IGNORE INTO CourseName (CID, Name) VALUES(%s,%s)"
s_insert_Message = "INSERT IGNORE INTO Message (MID,CID,Time,Title,Text) VALUES(%s,%s,DATE(%s),%s,%s)"
s_insert_UserCourse = "INSERT IGNORE INTO UserCourse (UID,CID) VALUES(%s,%s)"


def get_data_from_openid(openID):
    cur = cnx.cursor(buffered=True)
    cur.execute(s_get_data_by_openid, (openID,))
    for i in cur:
        return i


def isOpenIDBound(openID):
    return get_data_from_openid(openID) != None


def courseNameLoad():
    cur = cnx.cursor(buffered=True)
    cur.execute(s_get_courseName)
    for cid, name in cur:
        courseNameDict[cid] = name


def bind_user_openID(uid, upd, openID):
    cur = cnx.cursor(buffered=True)
    cur.execute(s_get_data_by_uid, (uid,))
    if (cur.rowcount != 0):
        return 2
    cur.execute(s_insert_UserInfo, (uid, upd, openID))
    cnx.commit()
    return 1 - cur.rowcount  # 0:success  1:failure


def store(d):
    cur = cnx.cursor(buffered=True)
    uid = int(d['_user']['username'])
    cur.execute(s_get_data_by_openid, (d['_user']['openID'],))
    for course in d['_courses']:
        cid = course['_id']
        cur.execute(s_insert_UserCourse, (uid, cid))
        cur.execute(s_insert_CourseName, (cid, course['_name']))
        for work in course['_works']:
            cur.execute(s_insert_Work, (work['_id'], cid, work['_end_time'], work['_title'], work['_details']))
            if work['_submitted'] == True:
                cur.execute(s_insert_WorkFinished, (uid, work['_id']))
        for msg in course['_messages']:
            cur.execute(s_insert_Message, (msg['_id'], cid, msg['_date'], msg['_title'], msg['_details']))
    cnx.commit()
    courseNameLoad()


def get_all_messages(openID):
    ret = []
    uid, upd = get_data_from_openid(openID)
    curC = cnx.cursor(buffered=True)
    curM = cnx.cursor(buffered=True)
    curC.execute(s_get_cid_by_uid, (uid,))
    for course in curC:
        if (course[0] == 126501):
            continue
        curM.execute(s_get_msg_by_cid, (course[0],))
        for msg in curM:
            # CID,Time,Title,Text
            elem = {'_Time': msg[1], '_Title': msg[2], '_CourseName': courseNameDict[msg[0]]}
            ret.append(elem)
    return ret


def get_messages_in_days(openID, days):
    ret = []
    uid, upd = get_data_from_openid(openID)
    curC = cnx.cursor(buffered=True)
    curM = cnx.cursor(buffered=True)
    curC.execute(s_get_cid_by_uid, (uid,))
    for course in curC:
        if (course[0] == 126501):
            continue
        curM.execute(s_get_msg_in_days, (course[0], days))
        for msg in curM:
            # CID,Time,Title,Text
            elem = {'_Time': msg[1], '_Title': msg[2], '_CourseName': courseNameDict[msg[0]], '_Text': msg[3]}
            ret.append(elem)
    return ret


def is_work_finished(uid, hid):
    cur = cnx.cursor(buffered=True)
    cur.execute(s_is_work_finished, (uid, hid))
    if cur.rowcount == 0:
        return False
    else:
        return True


def get_works_after_today(openID):
    ret = []
    uid, upd = get_data_from_openid(openID)
    curC = cnx.cursor(buffered=True)
    curW = cnx.cursor(buffered=True)
    curC.execute(s_get_cid_by_uid, (uid,))
    for course in curC:
        curW.execute(s_get_work_after, (course[0], date.today()))
        for work in curW:
            # print(work)
            # CID,EndTime,Title,WID
            elem = {'_EndTime': work[1], '_CourseName': courseNameDict[work[0]], '_Title': work[2],
                    '_Finished': is_work_finished(uid, work[3])}
            ret.append(elem)
    return ret

    # courseNameLoad()
