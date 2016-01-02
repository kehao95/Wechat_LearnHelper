__author__ = "kehao"
__email__ = "kehao95@gmail.com"

import sys
sys.path += ["./lib/aiolearn"]
from aiolearn import *
import db
import json
import asyncio
import logging
import requests

database = None
logging.basicConfig(level=logging.DEBUG)
__logger = logging.getLogger(__name__)




def push_new_items(items_dict, event_type):
    """
    if anything new in a course: file, message, work, etc
    push the information and all user data in this course to server
    request the server to push a template message to the users
    :param items_dict: [item]
    :param event_type: "new_messages","new_works"
    :return: data {"type","users","data"}
    """
    if not items_dict:
        return
    with open("address.txt", "r") as f:
        url = f.read()
    __logger.debug("get_server_address :%s" % url)
    for item in items_dict:
        course_name = database.get_course_name(item["course_id"])
        users = database.get_all_users(item["course_id"])
        item["course_name"] = course_name
        data = {"type": event_type, "users": users, "data": item}
        try:
            r = requests.post(url, json.dumps(data), timeout=0.02)
        except:
            __logger("push item connection timeout")


async def get_a_valid_user(course_id):
    """
    get a valid user for course
    if invalid update for next user
    if all users are invalid return none
    :param course_id:
    :return: User
    """
    async def update_user_for_course(course_id):
        for unkown_user in database.get_all_users(course_id):
            try:
                await User(unkown_user['username'], unkown_user['password']).login()
            except RuntimeError:
                continue
            else:
                # valid user
                database.set_user_for_course(course_id, unkown_user)
                u = User(unkown_user['username'], unkown_user['password'])
                return u
        else:
            # for loop done and no one is valid
            return None

    user = database.get_a_user(course_id)
    if user is None:
        return await update_user_for_course(course_id)

    u = User(user['username'], user['password'])
    try:
        await u.login()
    except RuntimeError:
        return await update_user_for_course(course_id)
    else:
        # valid user
        return u


async def update_courses():
    """
    update public information, fetch every courses once
    fetch all courses' works and messages, (new files)
    pick out the new ones
    :return:
    """
    __logger.debug("update_courses")
    # prepare a valid user for each course
    existing_courses_ids = database.get_all_courses()
    courses = []
    for course_id in existing_courses_ids:
        user = await get_a_valid_user(course_id)
        if user is None:
            continue
        else:
            courses.append(Course(user, course_id))
    __logger.debug("courses:%d" % len(courses))

    # fetch all works and messages of every course
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    messages = list(chain(*await asyncio.gather(*[course.messages for course in courses])))

    # pick out the new messages and works (whose ids are not in database yet)
    existing_works_ids = database.get_all_works()
    existing_messages_ids = database.get_all_messages()
    works_to_append = set()
    for work in works:
        if work.id not in existing_works_ids:
            existing_works_ids.add(work.id)
            works_to_append.add(work)
    __logger.debug("works_to_append: %d" % len(works_to_append))
    messages_to_append = set()
    for message in messages:
        if message.id not in existing_messages_ids:
            existing_messages_ids.add(message.id)
            messages_to_append.add(message)
    __logger.debug("messages_to_append: %d" % len(messages_to_append))

    # add the new messages and works to the database
    messages_dicts = list(await asyncio.gather(*[message.dict for message in messages_to_append]))
    works_dicts = list(await asyncio.gather(*[work.dict for work in works_to_append]))
    database.add_messages(messages_dicts)
    database.add_works(works_dicts)

    # push the new items to their users
    push_new_items(works_dicts, "new_works")
    push_new_items(messages_dicts, "new_messages")


async def update_completions():
    """
    update private information
    get every user's work completion information
    update them to database
    :return:
    """
    users = database.get_all_users()
    courses = []
    for user in users:
        courses_ids = database.get_all_courses(user)
        u = User(user['username'], user['password'])
        try:
            await u.login()
            for id in courses_ids:
                courses.append(Course(u, str(id)))
        except:
            # if user's password is not invalid anymore ignore him
            continue
    __logger.debug("courses: %r" % len(courses))
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    __logger.debug("works: %r" % len(works))
    completion = [(work.user.username, work.id) for work in works if work.completion]
    database.update_completion(completion)


async def main():
    while True:
        await update_courses()
        await update_completions()
        __logger.debug("wait for 20 seconds")
        await asyncio.sleep(20)


if __name__ == '__main__':
    with open(".secret.json", 'r') as f:
        db_secret = json.loads(f.read())['database']
        database = db.Database(username=db_secret['username'], password=db_secret['password'],
                               database=db_secret['database_name'], salt=db_secret['key'], address=db_secret['host'])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
