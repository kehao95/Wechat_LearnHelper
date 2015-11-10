__author__ = 'kehao'
import sys
import json
from json import JSONEncoder

sys.path += ["./lib", "./lib/wechat-python-sdk", "./lib/thu_learn"]
import thu_learn


class Spider:
    openID = None
    username = None
    password = None

    def __init__(self, openID, username, password):
        self.openID = openID
        self.username = username
        self.password = password
        if not thu_learn.login(username=self.username, password=self.password):
            raise KeyError("username&&password incorrect")

    def get_json(self):
        pass


class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


if __name__ == "__main__":
    result = ""
    thu_learn.login(user_id="***REMOVED***", user_pass="***REMOVED***")
    semester = thu_learn.Semester()
    result = MyEncoder().encode(semester)
    print(result)


    pass
