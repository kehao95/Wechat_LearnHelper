#!/usr/bin/python
# -*- coding: UTF-8 -*

from __future__ import print_function
from decimal import Decimal
from datetime import datetime, date, timedelta
import pymysql


class Database:
    S_GET_DATA_BY_OPENID = "SELECT UID,AES_DECRYPT(UPd,%s) FROM UserInfo WHERE OpenID = %s"
    S_GET_DATA_BY_UID = "SELECT UID,AES_DECRYPT(UPd,%s) FROM UserInfo WHERE UID = %s"
    S_GET_CID_BY_UID = "SELECT CID FROM UserCourse WHERE UID = %s"
    S_GET_USERS_BY_CID = "SELECT UserInfo.UID,AES_DECRYPT(UserInfo.UPd,%s),UserInfo.OpenID FROM UserCourse,UserInfo WHERE UserInfo.UID=UserCourse.UID AND UserCourse.CID=%s"
    S_GET_A_USER_BY_CID = "SELECT UserInfo.UID,AES_DECRYPT(UserInfo.UPd,%s),UserInfo.OpenID FROM CourseName,UserInfo WHERE UserInfo.UID=CourseName.UID AND CourseName.CID=%s"
    S_GET_MSG_BY_CID = "SELECT CID,Time,Title,Text FROM Message WHERE CID = %s"
    S_GET_MSG_IN_DAYS = "SELECT CID,Time,Title,Text FROM Message WHERE CID = %s AND DATE_SUB(CURDATE(),INTERVAL %s DAY) <= date(Time)"
    # S_GET_WORK_BY_CID = "SELECT CID,EndTime,Title,Text WHERE CID = %s"
    S_GET_COURSENAME = "SELECT CID,Name FROM CourseName"
    S_GET_NAME_FROM_CID = "SELECT Name FROM CourseName WHERE CID = %s"
    S_GET_WORK_AFTER = "SELECT CID,EndTime,Title,WID,Text FROM Work WHERE CID = %s AND EndTime > DATE(%s)"
    S_GET_ALL_USER = "SELECT UID, AES_DECRYPT(UPd,%s), OpenID FROM UserInfo"
    S_GET_ALL_UID = "SELECT UID FROM UserInfo"
    S_GET_ALL_MID = "SELECT MID FROM Message"
    S_GET_ALL_CID = "SELECT CID FROM CourseName"
    S_GET_ALL_WID = "SELECT WID FROM Work"

    S_IS_WORK_FINISHED = "SELECT WID FROM WorkFinished WHERE UID = %s AND WID = %s"

    S_INSERT_WORKFINISHED = "INSERT IGNORE INTO WorkFinished (UID,WID) VALUES(%s,%s)"
    S_INSERT_USERINFO = "INSERT IGNORE INTO UserInfo (UID,UPd,OpenID) VALUES (%s,AES_ENCRYPT(%s,%s),%s)"
    S_INSERT_WORK = "INSERT IGNORE INTO Work (WID, CID, EndTime, Title, Text) VALUES (%s,%s,DATE(%s),%s,%s)"
    S_INSERT_COURSENAME = "INSERT IGNORE INTO CourseName (CID, Name,UID) VALUES(%s,%s,%s)"
    S_INSERT_MESSAGE = "INSERT IGNORE INTO Message (MID,CID,Time,Title,Text) VALUES(%s,%s,DATE(%s),%s,%s)"
    S_INSERT_USERCOURSE = "INSERT IGNORE INTO UserCourse (UID,CID) VALUES(%s,%s)"

    S_CHANGE_PSW_BY_OPENID = "UPDATE IGNORE UserInfo SET UPd=AES_ENCRYPT(%s,%s) WHERE OpenID=%s"
    S_CHANGE_USER_FOR_COURSE = "UPDATE IGNORE UserCourse SET UID=%d WHERE CID=%d"

    S_DELETE_USER = "DELETE FROM UserInfo WHERE OpenID=%s"

    S_DATABASE_NAME = 'thu_learn'
    cnx = None
    key = "salt"    #AES加密用到的密钥

    courseNameDict = {} #缓存的课程名称【待处理】

    #mysql用户名，mysql密码，密钥，主机地址
    def __init__(self, username, password, salt='salt', address='127.0.0.1'):
        self.cnx = pymysql.connect(user=username, db=self.S_DATABASE_NAME, host=address, passwd=password,
                                   charset="utf8")
        self.courseNameLoad()
        self.key = salt

    #特殊函数，在已有的thu_learn数据库中建立表单
    def build_database(self):
        S_SET_UTF8 = "alter database %s character set utf8 collate utf8_unicode_ci"

        S_BUILD_COURSENAME = "create table CourseName (CID int primary key, Name varchar(30), UID int, UPd blob)"
        S_BUILD_WORK = "create table Work (WID int primary key, CID int, EndTime date, Text TEXT, Title varchar(63))"
        S_BUILD_MESSAGE = "create table Message (MID int primary key, CID int, Time date, Text TEXT, Title varchar(63))"
        S_BUILD_USERINFO = "create table UserInfo (UID int primary key, UPd blob, OpenID varchar(30))"
        S_BUILD_USERCOURSE = "create table UserCourse (UID int, CID int, primary key(UID, CID))"
        S_BUILD_WORKFINISHED = "create table WorkFinished (UID int, WID int, primary key(UID, WID))"

        cur = self.cnx.cursor()

        cur.execute(self.S_BUILD_COURSENAME)
        cur.execute(self.S_BUILD_MESSAGE)
        cur.execute(self.S_BUILD_WORK)
        cur.execute(self.S_BUILD_USERINFO)
        cur.execute(self.S_BUILD_USERCOURSE)
        cur.execute(self.S_BUILD_WORKFINISHED)
        # cur.execute(self.S_SET_UTF8, (self.S_DATABASE_NAME,))
        self.cnx.commit()

        # build_database()

    #####统一user类型 {'username': ,'password': ,'openid': }

    #将数据库返回的user信息转为传回的user-dict（主要对password解码。数据库blob形式在python中是b'str'# ）
    def build_user_dict(self, uid, upd, openid):
        return {'username': uid, 'password': upd.decode('utf8'), 'openid': openid}

    #从openid获取 （用户名，密码）
    def get_data_from_openid(self, openID):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_DATA_BY_OPENID, (self.key, openID))
        for i in cur:
            return i

    #从openid获取是否已经被绑定
    def isOpenIDBound(self, openID):
        return self.get_data_from_openid(openID) != None

    #初始化调用，获取课程名称
    def courseNameLoad(self):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_COURSENAME)
        for cid, name in cur:
            self.courseNameDict[cid] = name

    #绑定openid和uid以及upd
    def bind_user_openID(self, uid, upd, openID):
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_DATA_BY_UID, (self.key, uid))
        if (cur.rowcount != 0):
            return 2    #username used
        cur.execute(self.S_INSERT_USERINFO, (uid, upd, self.key, openID))
        self.cnx.commit()
        return 1 - cur.rowcount  # 0:success  1:database failure

    #修改密码。不会检验原来的密码
    def change_password(self, openID, upd):
        cur = self.cnx.cursor()
        cur.execute(self.S_CHANGE_PSW_BY_OPENID, (upd, self.key, openID))
        self.cnx.commit()
        if (cur.rowcount != 0):
            return 0    #success
        return 1        #failure

    #删除一条openid与userid的绑定信息
    def unbind_user_openID(self, openID):
        cur = self.cnx.cursor()
        cur.execute(self.S_DELETE_USER, (openID,))
        self.cnx.commit()

    #全部公告id的list
    def get_all_messages(self):
        ret = []
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_ALL_MID)
        for mid, in cur:
            ret.append(mid)
        return ret

    #全部作业id的list
    def get_all_works(self):
        ret = []
        cur = self.cnx.cursor()
        cur.execute(self.S_GET_ALL_WID)
        for wid, in cur:
            ret.append(wid)
        return ret

    #0参数：全部课程id的list
    #1个int识别为userid, 返回user的课程id的list
    #1个user-dict，userid为user['username']，返回user的课程id的list
    def get_all_courses(self, user=-1):
        ret = []
        cur = self.cnx.cursor()
        if (user == -1):
            cur.execute(self.S_GET_ALL_CID)
        else:
            if isinstance(user, int):
                uid = user
            else:
                uid = user['username']
            cur.execute(self.S_GET_CID_BY_UID, (uid,))
        for cid, in cur:
            ret.append(cid)
        return ret

    #0参数：全username的list
    #1参数：对courseid取选课的username的list
    def get_all_users(self, courseid=-1):
        ret = []
        cur = self.cnx.cursor()
        if (courseid == -1):
            cur.execute(self.S_GET_ALL_USER, (self.key,))
        else:
            cur.execute(self.S_GET_USERS_BY_CID, (self.key, courseid))
        for user in cur:
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

    #[{id,user,id,name}]    其中user是user-dict,会被当成缓存的user
    def add_courses(self, courselist):
        cur = self.cnx.cursor()
        for course in courselist:
            uid = course['user']['username']
            cur.execute(self.S_INSERT_COURSENAME, (course['id'], course['name'], uid))
            # cur.execute(self.S_INSERT_USERCOURSE, (course['id'],uid))
            self.courseNameDict[course['id']] = course['name']
        self.cnx.commit()

    #[(uid,cid)]
    def add_user_course(self, courselist):
        cur = self.cnx.cursor()
        for uid, cid in courselist:
            cur.execute(self.S_INSERT_USERCOURSE, (uid, cid))
        self.cnx.commit()

    #[{id,course_id,date,title,detail}]
    def add_messages(self, msglist):
        cur = self.cnx.cursor()
        for msg in msglist:
            cur.execute(self.S_INSERT_MESSAGE, (
                msg['id'], msg['course_id'], msg['date'], msg['title'], msg['detail']))  # (MID,CID,Time,Title,Text)
        self.cnx.commit()

    #[{id,course_id,end_time,title,detail}]
    def add_works(self, worklist):
        cur = self.cnx.cursor()
        for work in worklist:
            cur.execute(self.S_INSERT_WORK,
                        (work['id'], work['course_id'], work['end_time'], work['title'], work['detail']))
        self.cnx.commit()

    #[(uid, wid)]
    def update_completion(self, completionlist):
        cur = self.cnx.cursor()
        for uid, wid in completionlist:
            cur.execute(self.S_INSERT_WORKFINISHED, (uid, wid))
        self.cnx.commit()

    """
    def store(self, d):
        cur = self.cnx.cursor()
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
        #courseNameLoad()


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
        uid, upd = self.get_data_from_openid(openID)
        curC = self.cnx.cursor()
        curM = self.cnx.cursor()
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

    def is_work_finished(self, uid, wid):
        cur = self.cnx.cursor()
        cur.execute(self.S_IS_WORK_FINISHED, (uid, wid))
        if cur.rowcount == 0:
            return False
        else:
            return True

    def get_works_after_today(self, openID):
        ret = []
        uid, upd = self.get_data_from_openid(openID)
        curC = self.cnx.cursor()
        curW = self.cnx.cursor()
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
