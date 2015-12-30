__author__ = "kehao"
__email__ = "kehao95@gmail.com"

from aiolearn import *
import db
import json
import asyncio
import logging
import requests

database = None
logging.basicConfig(level=logging.DEBUG)
__logger = logging.getLogger(__name__)

def get_users():
    """
    get users which registered moments ago
    using file to transfer the data
    :return: users dict list
    """
    users = database.get_all_new_users()
    """
    users = []
    __logger.debug("get_users")
    try:
        with open("newusers.json", 'r') as f:
            users = json.loads(f.read())
        open("newusers.json", 'w').close()
    except:
        __logger.debug("could not open 'newusers.json'")
        pass
    """
    return users



def push_ok(users):
    """
    push registering done messages to server
    data = {"type": "register_done", "users": users}
    :param users:
    :return: a request to server
    """
    if not users:
        return None
    __logger.debug("get_server_address")
    with open("address.txt", "r") as f:
        url = f.read()
    data = {"type": "register_done", "users": users}
    requests.post(url, json.dumps(data))


async def update_database():
    """
    main register loop
    fetch all information of the users' courses
    push them to database
    :return:
    """
    __logger.debug("update database")

    # prepare users
    users = get_users()
    Users = []
    for user in users:
        database.bind_user_openID(user['username'], user['password'], user['openid'])
        Users.append(User(user['username'], user['password']))

    # fetch everything courses, works, messages ...
    semesters = [Semester(user) for user in Users]
    courses = list(chain(*await asyncio.gather(*[semester.courses for semester in semesters])))
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    messages = list(chain(*await asyncio.gather(*[course.messages for course in courses])))

    # pick out which are not in the database
    existing_works_ids = database.get_all_works()  # TODO
    existing_messages_ids = database.get_all_messages()
    existing_courses_ids = database.get_all_courses()
    courses_to_append = []
    for course in courses:
        if course.id not in existing_courses_ids:
            existing_courses_ids.add(course.id)
            courses_to_append.append(course)
    __logger.debug(" courses_to_append: %d" % len(courses_to_append))
    works_to_append = []
    for work in works:
        if work.id not in existing_works_ids:
            existing_works_ids.add(work.id)
            works_to_append.append(work)
    __logger.debug("   works_to_append: %d" % len(works_to_append))
    messages_to_append = []
    for message in messages:
        if message.id not in existing_messages_ids:
            existing_messages_ids.add(message.id)
            messages_to_append.append(message)
    __logger.debug("messages_to_append: %d" % len(messages_to_append))

    # add them to database
    courses_dicts = [course.dict for course in courses_to_append]
    messages_dicts = list(await asyncio.gather(*[message.dict for message in messages_to_append]))
    works_dicts = list(await asyncio.gather(*[work.dict for work in works_to_append]))
    user_course = [(course.user.username, course.id) for course in courses]
    completion = [(work.user.username, work.id) for work in works if work.completion]
    database.add_courses(courses_dicts)
    database.add_messages(messages_dicts)
    database.add_works(works_dicts)
    database.update_completion(completion)
    database.add_user_course(user_course)
    __logger.debug("insert     courses: %d" % len(courses_dicts))
    __logger.debug("insert    messages: %d" % len(messages_dicts))
    __logger.debug("insert       works: %d" % len(works_dicts))
    __logger.debug("insert  completion: %d" % len(completion))
    __logger.debug("insert user_course: %d" % len(user_course))
    # push register done messages
    push_ok(users)


async def main():
    while True:
        await  asyncio.gather(update_database())
        print("wait for another 3 seconds")
        await asyncio.sleep(3)
        print("let's do it again!")


if __name__ == "__main__":
    with open(".secret.json", 'r') as f:
        db_secret = json.loads(f.read())['database']
        database = db.Database(username=db_secret['username'], password=db_secret['password'],
                               database=db_secret['database_name'], salt=db_secret['key'], address=db_secret['host'])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
