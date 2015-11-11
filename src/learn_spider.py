__author__ = 'kehao'
import sys
import json
from json import JSONEncoder

sys.path += ["./lib", "./lib/wechat-python-sdk", "./lib/thu_learn"]
import thu_learn
import database


class Spider:
    openID = None
    username = None
    password = None

    def __init__(self, openID, username, password):
        self.openID = openID
        self.username = username
        self.password = password
        if not thu_learn.login(self.username, self.password):
            raise KeyError("username&&password incorrect")

    def get_dict(self):
        semester = thu_learn.Semester()
        result = MyEncoder().encode(semester)
        result = json.loads(result)
        result["_user"] = {"openID":self.openID,
                          "username":self.username,
                          "password":self.password}

        return result


class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


if __name__ == "__main__":
    kehao = Spider(openID="0", username="***REMOVED***", password="***REMOVED***")
    database.bind_user_openID(kehao.username,kehao.password,kehao.openID)
    #database.store(kehao.get_dict())
    #database.store(kehao.get_dict())
    #database.store(kehao.get_dict())
    aaaa = 0
    zhc = Spider(openID="3", username="***REMOVED***", password="***REMOVED***")
    database.bind_user_openID(zhc.username,zhc.password,zhc.openID)
    #database.store(zhc.get_dict())
    #database.store(zhc.get_dict())
    lss = Spider(openID="1", username="***REMOVED***", password="***REMOVED***")
    database.bind_user_openID(lss.username,lss.password,lss.openID)
    #database.store(lss.get_dict())
    #database.store(lss.get_dict())

    print(database.get_all_messages('3'))
    print(1)

    """
    thu_learn.login(user_id="***REMOVED***", user_pass="***REMOVED***")
    semester = thu_learn.Semester()
    result = MyEncoder().encode(semester)
    print(result)
    """