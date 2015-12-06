__author__ = "kehao"
__email__ = "kehao95@gmail.com"

from aiolearn import *
import asyncio
import requests
import json
import db

database = None


def push_new_items(items_dict, event_type):
    if not items_dict:
        return
    logger.debug("get_server_address")
    with open("address.txt", "r") as f:
        url = f.read()
    for item in items_dict:
        course_name = database.get_course_name(item["course_id"])
        users = database.get_all_users(item["course_id"])
        item["course_name"] = course_name
        data = {"type": event_type, "users": users, "data": item}
        requests.post(url, json.dumps(data))


async def get_a_valid_user(course_id):
    """
    get a valid user for course
    if invalid update for next user
    if all users are invalid return none
    :param course_id:
    :return: User
    """
    user = database.get_a_user(course_id)
    u = User(user['username'], user['password'])
    try:
        await u.login()
    except RuntimeError:
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
    else:
        # valid user
        return u


async def update_courses():
    existing_works_ids = database.get_all_works()  # TODO
    existing_messages_ids = database.get_all_messages()
    existing_courses_ids = database.get_all_courses()
    courses = []
    for course_id in existing_courses_ids:
        user = await get_a_valid_user(course_id)
        print((user.username, course_id))
        if user is None:
            continue
        else:
            courses.append(Course(user, course_id))
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    messages = list(chain(*await asyncio.gather(*[course.messages for course in courses])))

    works_to_append = set()
    for work in works:
        if work.id not in existing_works_ids:
            existing_works_ids.add(work.id)
            works_to_append.add(work)
    logger.debug(len(works_to_append))

    messages_to_append = set()
    for message in messages:
        if message.id not in existing_messages_ids:
            existing_messages_ids.add(message.id)
            messages_to_append.add(message)
    logger.debug(len(messages_to_append))

    messages_dicts = list(await asyncio.gather(*[message.dict for message in messages_to_append]))
    works_dicts = list(await asyncio.gather(*[work.dict for work in works_to_append]))
    database.add_messages(messages_dicts)
    database.add_works(works_dicts)
    # TODO
    push_new_items(works_dicts, "new_works")
    push_new_items(messages_dicts, "new_messages")


async def update_completions():
    users = database.get_all_users()
    courses = []
    for user in users:
        courses_ids = database.get_all_courses(user)
        u = User(user['username'], user['password'])
        await u.login()
        for id in courses_ids:
            courses.append(Course(u, str(id)))
    logger.debug("courses: %r" % len(courses))
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    logger.debug("works: %r" % len(works))
    completion = [(work.user.username, work.id) for work in works if work.completion]
    database.update_completion(completion)


async def main():
    while True:
        await update_courses()
        await update_completions()
        await asyncio.sleep(10)


if __name__ == '__main__':
    with open(".secret.json", 'r') as f:
        db_secret = json.loads(f.read())['database']
        database = db.Database(username=db_secret['username'], password=db_secret['password'],
                               database=db_secret['database_name'], salt=db_secret['key'], address=db_secret['host'])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
