import sys
import json
from json import JSONEncoder
import asyncio

sys.path += ["./lib", "./lib/thu_learn"]
import learn

userQ = asyncio.Queue()


async def update_users_list():
    users = DB.GET_ALL_USERS()  # user.id user.pass
    for user in users:
        userQ.put(user)


async def update_db():
    async def update_messages_works():
        """
        this will update all the works and messages of courses in the DataBase
        :return:
        """
        courses_id = DB.get_all_courses()
        messages_id = DB.get_all_messages()
        works_id  = DB.get_all_works()
        for id in courses_id:
            user = DB.get_vaild_user()
            learn.login(user.username, user.password)
            course = learn.Course(id)
            for message in course.messages:
                if message.id not in messages_id:
                    m = JSON(message)
                    DB.add_message(m)
            for work in course.works:
                if work.id not in works_id:
                    w = JSON(work)
                    DB.add_work(w)

    async def update_users():
        """
        this will update all the user's homework status
        :return:
        """
        users = DB.get_all_users()
        for user in users:
            login(user)
            for work in




asyncio.Task(update_users_list())
asyncio.Task(update_db())
