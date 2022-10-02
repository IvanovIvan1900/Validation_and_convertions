import datetime as dt

import pytest


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.created_at = dt.datetime.now()

    def __repr__(self):
        return "<User(name={self.name!r})>".format(self=self)

@pytest.fixture
def user_1():
    return User(name="Monty", email="monty@python.org")

@pytest.fixture
def user_2_dict():
    return {
    "created_at": "2014-08-11T05:26:03.869245",
    "email": "ken@yahoo.com",
    "name": "Ken",
    }

@pytest.fixture
def user_2_dict_wichout_created_at():
    return {
    "email": "ken@yahoo.com",
    "name": "Ken",
    }

class Client:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.created_at = dt.datetime.now()
        self.tasks = []


class Task:
    def __init__(self, title):
        self.title = title


@pytest.fixture
def clien_wich_two_tasks():
    task_1 = Task("First task")
    task_2 = Task("Two task")
    client = Client('Test client', 'test@mail.ru')
    client.tasks.append(task_1)
    client.tasks.append(task_1)

    return client