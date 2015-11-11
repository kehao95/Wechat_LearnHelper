import pickle


class User:
    openID = None
    username = None
    password = None

    def __init__(self, openID=None, username=None, password=None):
        self.openID = openID
        self.username = username
        self.password = password


class DB():
    file = "USER_database"
    data = {}

    def __init__(self):
        pass
        self._load()

    def _load(self):
        with open(self.file, "rb") as f:
            self.data = pickle.load(f)

    def _save(self):
        with open(self.file, "wb") as f:
            pickle.dump(self.data, f)

    def save_user(self, user):
        print(user)
        self.data[user.openID] = {"username": user.username,
                                  "password": user.password}
        self._save()

    def find_by_openID(self, openID) -> User:
        self._load()
        if openID in self.data:
            username = self.data[openID]["username"]
            password = self.data[openID]["password"]
            return User(openID=openID, username=username, password=password)
        else:
            return None


db = DB()


def add_user(openID, username, password):
    user = User(openID, username, password)
    db.save_user(user)


def find_by_openID(openID):
    if isinstance(db.find_by_openID(openID), User):
        return True
    else:
        return False


def develop():
    add_user("1", "kehao", "kehao")
    add_user("2", "kehao2", "kehao2")
    add_user("3", "kehao3", "kehao3")
    add_user("4", "kehao4", "kehao4")
    for i in range(10):
        if find_by_openID(str(i)):
            print("openID:%d in database"%i)
        else:
            print("openID:%d not in database"%i)


if __name__ == "__main__":
    develop()
