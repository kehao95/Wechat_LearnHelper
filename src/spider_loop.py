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
    Users = []
    for user in users:
        Users.append(User(user['username'], user['password']))
    semesters = [Semester(user) for user in Users]
    courses = list(chain(*await asyncio.gather(*[semester.courses for semester in semesters])))
    works = list(chain(*await asyncio.gather(*[course.works for course in courses])))
    messages = list(chain(*await asyncio.gather(*[course.messages for course in courses])))

    worksids = [(work.id, work) for work in works]
    messagesids = [(messages.id, messages) for messages in messages]
    completion = [(work.user.username, work.id) for work in works if work.completion]
    print(">>>")
    print(worksids)
    print(messagesids)
    print(completion)
    await asyncio.sleep(100)


async def main():
    while True:
        await  asyncio.gather(update_database())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
