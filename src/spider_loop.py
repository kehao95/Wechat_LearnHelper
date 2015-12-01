__author__ = "kehao"
__email__ = "kehao95@gmail.com"

from aiolearn import *
import asyncio
import json


def get_users():
    logger.debug("get_users")
    with open(".secret.json", 'r') as f:
        secret = json.loads(f.read())
        users = secret['users']
    return users


async def update_database():
    logger.debug("database")
    users = get_users()
    existing_works_ids = []
    existing_messages_ids = []
    existing_courses_ids = []
    Users = []
    for user in users:
        Users.append(User(user['username'], user['password']))
    semesters = [Semester(user) for user in Users]
    courses = list(chain(*await asyncio.gather(*[semester.courses for semester in semesters])))
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    messages = list(chain(*await asyncio.gather(*[course.messages for course in courses])))


    courses_to_append =[]
    for course in courses:
        if course.id not in existing_courses_ids:
            existing_courses_ids.append(course.id)
            courses_to_append.append(course)
    logger.debug(len(courses_to_append))

    works_to_append = []
    for work in works:
        if work.id not in existing_works_ids:
            existing_works_ids.append(work.id)
            works_to_append.append(work)
    logger.debug(len(works_to_append))

    messages_to_append = []
    for message in messages:
        if message.id not in existing_messages_ids:
            existing_messages_ids.append(message.id)
            messages_to_append.append(message)
    logger.debug(len(messages_to_append))


    courses_dicts = [course.__dict__ for course in courses_to_append]
    messages_dicts = list(await asyncio.gather(*[message.dict for message in messages_to_append]))
    works_dicts = list(await asyncio.gather(*[work.dict for work in works_to_append]))
    completion = [(work.user.username, work.id) for work in works if work.completion]
    user_course = [(course.user.username, courses.id) for course in courses]
    print("end")
    await asyncio.sleep(100)


async def main():
    while True:
        await  asyncio.gather(update_database())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
