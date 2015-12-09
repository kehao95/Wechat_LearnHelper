#!/usr/bin/python
# -*- coding: UTF-8 -*

from __future__ import print_function
from decimal import Decimal
from datetime import datetime, date, timedelta
import pymysql
import logging


class Database:
    S_GET_DATA_BY_OPENID = "SELECT SQL_NO_CACHE UID,AES_DECRYPT(UPd,%s) FROM UserInfo WHERE OpenID = %s"
    S_GET_DATA_BY_UID = "SELECT SQL_NO_CACHE UID,AES_DECRYPT(UPd,%s) FROM UserInfo WHERE UID = %s"
    S_GET_STATUS_BY_OPENID = "SELECT SQL_NO_CACHE Status FROM UserInfo WHERE OpenID = %s"
    S_GET_STATUS_BY_UID = "SELECT SQL_NO_CACHE Status FROM UserInfo WHERE UID = %s"
    S_GET_CID_BY_UID = "SELECT SQL_NO_CACHE CID FROM UserCourse WHERE UID = %s"
    S_GET_USERS_BY_CID = "SELECT SQL_NO_CACHE UserInfo.UID,AES_DECRYPT(UserInfo.UPd,%s),UserInfo.OpenID FROM UserCourse,UserInfo WHERE UserInfo.UID=UserCourse.UID AND UserCourse.CID=%s"
    S_GET_A_USER_BY_CID = "SELECT SQL_NO_CACHE UserInfo.UID,AES_DECRYPT(UserInfo.UPd,%s),UserInfo.OpenID FROM CourseName,UserInfo WHERE UserInfo.UID=CourseName.UID AND CourseName.CID=%s"
    S_GET_MSG_BY_CID = "SELECT SQL_NO_CACHE CID,Time,Title,Text FROM Message WHERE CID = %s"
    S_GET_MSG_IN_DAYS = "SELECT SQL_NO_CACHE CID,Time,Title,Text FROM Message WHERE CID = %s AND DATE_SUB(CURDATE(),INTERVAL %s DAY) <= date(Time)"
    # S_GET_WORK_BY_CID = "SELECT SQL_NO_CACHE CID,EndTime,Title,Text WHERE CID = %s"
    S_GET_COURSENAME = "SELECT SQL_NO_CACHE CID,Name FROM CourseName"
    S_GET_COURSENAME_BY_UID = "SELECT SQL_NO_CACHE Name FROM CourseName WHERE CID = %s"
    S_GET_NAME_FROM_CID = "SELECT SQL_NO_CACHE Name FROM CourseName WHERE CID = %s"
    S_GET_WORK_AFTER = "SELECT SQL_NO_CACHE CID,EndTime,Title,WID,Text FROM Work WHERE CID = %s AND EndTime > DATE(%s)"
    S_GET_ALL_USER = "SELECT SQL_NO_CACHE UID, AES_DECRYPT(UPd,%s), OpenID FROM UserInfo"
    S_GET_ALL_UID = "SELECT SQL_NO_CACHE UID FROM UserInfo"
    S_GET_ALL_MID = "SELECT SQL_NO_CACHE MID FROM Message"
    S_GET_ALL_CID = "SELECT SQL_NO_CACHE CID FROM CourseName"
    S_GET_ALL_WID = "SELECT SQL_NO_CACHE WID FROM Work"
    S_GET_DATA_DELETE_USER = "SELECT SQL_NO_CACHE UID,OpenID FROM UserInfo WHERE Status = 2"

    S_IS_WORK_FINISHED = "SELECT SQL_NO_CACHE WID FROM WorkFinished WHERE UID = %s AND WID = %s"

    S_INSERT_WORKFINISHED = "INSERT IGNORE INTO WorkFinished (UID,WID) VALUES(%s,%s)"
    S_INSERT_USERINFO = "INSERT IGNORE INTO UserInfo (UID,UPd,OpenID,Status) VALUES (%s,AES_ENCRYPT(%s,%s),%s,1)"
    S_INSERT_WORK = "INSERT IGNORE INTO Work (WID, CID, EndTime, Title, Text) VALUES (%s,%s,DATE(%s),%s,%s)"
    S_INSERT_COURSENAME = "INSERT IGNORE INTO CourseName (CID, Name,UID) VALUES(%s,%s,%s)"
    S_INSERT_MESSAGE = "INSERT IGNORE INTO Message (MID,CID,Time,Title,Text) VALUES(%s,%s,DATE(%s),%s,%s)"
    S_INSERT_USERCOURSE = "INSERT IGNORE INTO UserCourse (UID,CID) VALUES(%s,%s)"

    S_CHANGE_PSW_BY_OPENID = "UPDATE IGNORE UserInfo SET UPd=AES_ENCRYPT(%s,%s) WHERE OpenID=%s"
    S_CHANGE_USER_FOR_COURSE = "UPDATE IGNORE UserCourse SET UID=%d WHERE CID=%d"
    S_CHANGE_USER_BY_UID = "UPDATE IGNORE UserInfo SET UPd=AES_ENCRYPT(%s,%s),OpenID=%s,Status=1 WHERE UID=%s"
    S_CHANGE_USER_BY_OPENID = "UPDATE IGNORE UserInfo SET UID=%s,UPd=AES_ENCRYPT(%s,%s),Status=1 WHERE OpenID=%s"
    S_SET_STATUS_BY_OPENID = "UPDATE IGNORE UserInfo SET Status=%s WHERE OpenID=%s"
    S_SET_STATUS_BY_UID = "UPDATE IGNORE UserInfo SET Status=%s WHERE UID=%s"

    S_DELETE_USER = "DELETE FROM UserInfo WHERE OpenID=%s"
    S_DELETE_USERCOURSE_BY_USER = "DELETE FROM UserCourse WHERE UID=%s"

    STATUS_OK = 0
    STATUS_NOT_FOUND = -1
    STATUS_WAITING = 1
    STATUS_DELETE = 2

    cnx = None
    key = "salt"  # AES加密用到的密钥

    #courseNameDict = {}  # 缓存的课程名称【待处理】

    # mysql用户名，mysql密码，数据库，密钥，主机地址
    def __init__(self, username, password, database, salt='salt', address='127.0.0.1'):
        logging.debug("connecting to mysql server")
        self.cnx = pymysql.connect(user=username, db=database, host=address, passwd=password,
                                   charset="utf8")
        self.cnx.autocommit(True)
        logging.debug("connection established")
        #self.courseNameLoad()
        self.key = salt

    # 特殊函数，在已有的thu_learn数据库中建立表单
    def build_database(self):
        S_SET_UTF8 = "alter database %s character set utf8 collate utf8_unicode_ci"

        S_BUILD_COURSENAME = "create table CourseName (CID int primary key, Name varchar(30), UID int, UPd blob)"
        S_BUILD_WORK = "create table Work (WID int primary key, CID int, EndTime date, Text TEXT, Title varchar(63))"
        S_BUILD_MESSAGE = "create table Message (MID int primary key, CID int, Time date, Text TEXT, Title varchar(63))"
        S_BUILD_USERINFO = "create table UserInfo (UID int primary key, UPd blob, OpenID varchar(30), Status int)"
        S_BUILD_USERCOURSE = "create table UserCourse (UID int, CID int, primary key(UID, CID))"
        S_BUILD_WORKFINISHED = "create table WorkFinished (UID int, WID int, primary key(UID, WID))"

        ###注：Status标记用户状态。其中,0:正常，1:等待第一次 2:等待删除。-1：数据库中没有这个用户

        cur = self.cnx.cursor()

        cur.execute(S_BUILD_COURSENAME)
        cur.execute(S_BUILD_MESSAGE)
        cur.execute(S_BUILD_WORK)
        cur.execute(S_BUILD_USERINFO)
        cur.execute(S_BUILD_USERCOURSE)
        cur.execute(S_BUILD_WORKFINISHED)
        # cur.execute(self.S_SET_UTF8, (self.S_DATABASE_NAME,))
        self.cnx.commit()

        # build_database()

    #####统一user类型 {'username': ,'password': ,'openid': }

    # 将数据库返回的user信息转为传回的user-dict（主要对password解码。数据库blob形式在python中是b'str'# ）
    def build_user_dict(self, uid, upd, openid):
        return {'username': uid, 'password': upd.decode('utf8'), 'openid': openid}

    def get_course_name(self, cid):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_COURSENAME_BY_UID, (cid,))
        for i, in cur:
            return i
        return ""

    # 从openid获取 （用户名，密码）
    def get_data_by_openid(self, openID):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_DATA_BY_OPENID, (self.key, openID))
        for i in cur:
            return i

    def get_user_by_username(self, uid):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_DATA_BY_UID, (self.key, uid))
        for i in cur:
            return i

    def get_status_by_username(self, uid):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_STATUS_BY_UID, (uid,))
        if cur.rowcount == 0:
            return self.STATUS_NOT_FOUND
        for i in cur:
            return i[0]

    def get_status_by_openid(self, openID):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_STATUS_BY_OPENID, (openID,))
        if cur.rowcount == 0:
            return self.STATUS_NOT_FOUND
        for i in cur:
            return i[0]

    def set_status_by_openid(self, openID, status):
        cur = self.cnx.cursor()
        cur.execute(self.S_SET_STATUS_BY_OPENID, (status, openID))

    def set_status_by_username(self, uid, status):
        cur = self.cnx.cursor()
        cur.execute(self.S_SET_STATUS_BY_UID, (status, uid))

    # 从openid获取是否就绪
    def isOpenIDAvailable(self, openID):
        return self.get_status_by_openid(openID) == self.STATUS_OK

    # 从openid获取是否已经被绑定
    def isOpenIDBound(self, openID):
        r = self.get_status_by_openid(openID)
        return r == self.STATUS_OK or r == self.STATUS_WAITING

    def set_openid_ok(self, openID):
        self.set_status_by_openid(openID, self.STATUS_OK)

    def set_openid_delete(self, openID):
        self.set_status_by_openid(openID, self.STATUS_OK)

        # 初始化调用，获取课程名称

#    def courseNameLoad(self):
#        cur = self.cnx.cursor()
#        cur.execute(self.S_GET_COURSENAME)
#        for cid, name in cur:
#            Database.courseNameDict[cid] = name

    # 绑定openid和uid以及upd
    def bind_user_openID(self, uid, upd, openID):
        r = self.get_status_by_username(uid)
        cur = self.cnx.cursor()
        if r == self.STATUS_OK or r == self.STATUS_WAITING:
            return 2
        elif r == self.STATUS_DELETE:
            cur.execute(self.S_CHANGE_USER_BY_UID, (upd, self.key, openID, uid))
            # logging.debug("find uid delete")
        elif r == self.STATUS_NOT_FOUND:
            if self.get_status_by_openid(openID) == self.STATUS_NOT_FOUND:
                # logging.debug("no openid")
                cur.execute(self.S_INSERT_USERINFO, (uid, upd, self.key, openID))
            else:
                # logging.debug("find openid delete")
                uid, upd = self.get_data_by_openid(openID)
                cur.execute(self.S_DELETE_USERCOURSE_BY_USER, (uid, ))
                cur.execute(self.S_CHANGE_USER_BY_OPENID, (uid, upd, self.key, openID))
        self.cnx.commit()
        return 1 - cur.rowcount  # 0:success  1:database failure

    # 修改密码。不会检验原来的密码
    def change_password(self, openID, upd):
        cur = self.cnx.cursor()
        cur.execute(self.S_CHANGE_PSW_BY_OPENID, (upd, self.key, openID))
        self.cnx.commit()
        if (cur.rowcount != 0):
            return 0  # success
        return 1  # failure

    # 把一条openid与userid的绑定信息标记为删除
    def unbind_user_openID(self, openID):
        self.set_status_by_openid(openID, self.STATUS_DELETE)

    def delete_user(self):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_DATA_DELETE_USER)
        cur2 = self.cnx.cursor()
        for uid, openID in cur:
            cur2.execute(self.S_DELETE_USER, (uid,))
            cur2.execute(self.S_DELETE_USERCOURSE_BY_USER, (uid,))

    # 全部公告id的set
    def get_all_messages(self):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_ALL_MID)
        ret = set(map(str, [mid for mid, in cur]))
        return ret

    # 全部作业id的set
    def get_all_works(self):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_ALL_WID)
        ret = set(map(str, [cid for cid, in cur]))
        return ret

    # 0参数：全部课程id的set
    # 1个int识别为userid, 返回user的课程id的set
    # 1个user-dict，userid为user['username']，返回user的课程id的set
    def get_all_courses(self, user=-1):
        cur = self.cnx.cursor()
        if (user == -1):
            cur.execute(self.S_GET_ALL_CID)
        else:
            if isinstance(user, int):
                uid = user
            else:
                uid = user['username']
            cur.execute(self.S_GET_CID_BY_UID, (uid,))
        ret = set(map(str, [cid for cid, in cur]))
        return ret

    # 0参数：全username的list
    # 1参数：对courseid取选课的username的list
    def get_all_users(self, courseid=-1):
        ret = []
        cur = self.cnx.cursor()
        if (courseid == -1):
            cur.execute(self.S_GET_ALL_USER, (self.key,))
        else:
            cur.execute(self.S_GET_USERS_BY_CID, (self.key, courseid))
        for user in cur:
            if self.get_status_by_username(user[0]) == self.STATUS_OK:
                ret.append(self.build_user_dict(user[0], user[1], user[2]))
        return ret

    #####已知courseid，获取一个缓存的user-dict信息
    def get_a_user(self, courseid):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_A_USER_BY_CID, (self.key, courseid))
        for user in cur:
            return self.build_user_dict(user[0], user[1], user[2])

    #####更新courseid的缓存user信息
    def set_user_for_course(self, courseid, user):
        cur = self.cnx.cursor()
        cur.execute(self.S_CHANGE_USER_FOR_COURSE, (courseid, user['username']))

    # [{id,user,id,name}]    其中user是user-dict,会被当成缓存的user
    def add_courses(self, courselist):
        cur = self.cnx.cursor()
        for course in courselist:
            uid = course['user']['username']
            cur.execute(self.S_INSERT_COURSENAME, (course['id'], course['name'], uid))
            # cur.execute(self.S_INSERT_USERCOURSE, (course['id'],uid))
            #Database.courseNameDict[course['id']] = course['name']
        self.cnx.commit()

    # [(uid,cid)]
    def add_user_course(self, courselist):
        cur = self.cnx.cursor()
        for uid, cid in courselist:
            cur.execute(self.S_INSERT_USERCOURSE, (uid, cid))
        self.cnx.commit()

    # [{id,course_id,date,title,detail}]
    def add_messages(self, msglist):
        cur = self.cnx.cursor()
        for msg in msglist:
            cur.execute(self.S_INSERT_MESSAGE, (
                msg['id'], msg['course_id'], msg['date'], msg['title'], msg['detail']))  # (MID,CID,Time,Title,Text)
        self.cnx.commit()

    # [{id,course_id,end_time,title,detail}]
    def add_works(self, worklist):
        cur = self.cnx.cursor()
        for work in worklist:
            cur.execute(self.S_INSERT_WORK,
                        (work['id'], work['course_id'], work['end_time'], work['title'], work['detail']))
        self.cnx.commit()

    # [(uid, wid)]
    def update_completion(self, completionlist):
        cur = self.cnx.cursor()
        for uid, wid in completionlist:
            cur.execute(self.S_INSERT_WORKFINISHED, (uid, wid))
        self.cnx.commit()

    """
    def get_all_messages(self, openID):
        ret = []
        uid, upd = self.get_data_from_openid(openID)
        curC = self.cnx.cursor()
        curM = self.cnx.cursor()
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
    """


    def get_messages_in_days(self, openID, days):
        ret = []
        uid, upd = self.get_data_by_openid(openID)
        curC = self.cnx.cursor()
        curM = self.cnx.cursor()
        curC.execute(self.S_GET_CID_BY_UID, (uid,))
        for course in curC:
            if (course[0] == 126501):
                continue
            curM.execute(self.S_GET_MSG_IN_DAYS, (course[0], days))
            for msg in curM:
                # CID,Time,Title,Text
                elem = {'_Time': msg[1], '_Title': msg[2], '_CourseName': self.get_course_name([msg[0]]), '_Text': msg[3]}
                ret.append(elem)
        return ret

    def is_work_finished(self, uid, wid):
        cur = self.cnx.cursor()
        cur.execute(self.S_IS_WORK_FINISHED, (uid, wid))
        if cur.rowcount == 0:
            return False
        else:
            return True

    def get_works_after_today(self, openID):
        ret = []
        uid, upd = self.get_data_by_openid(openID)
        curC = self.cnx.cursor()
        curW = self.cnx.cursor()
        curC.execute(self.S_GET_CID_BY_UID, (uid,))
        for course in curC:
            curW.execute(self.S_GET_WORK_AFTER, (course[0], date.today()))
            for work in curW:
                # print(work)
                # CID,EndTime,Title,WID,Text
                elem = {'_EndTime': work[1], '_CourseName': self.get_course_name([work[0]]), '_Title': work[2],
                        '_Finished': self.is_work_finished(uid, work[3]), '_Text': work[4]}
                ret.append(elem)
        return ret


if __name__ == "__main__":
    db = Database()
