# -*- coding: utf-8 -*-
from functools import wraps

from flask import request, abort
from flask_login import LoginManager, UserMixin

from .config import cfg
from .db import RunnerDB

login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, name, id):
        self.name = name
        self.id = id


@login_manager.user_loader
def user_loader_callback(id):
    db = RunnerDB(cfg.db_file)
    user = db.find_user_by_id(id)
    return User(user.get('username'), id)


def apikey_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        db = RunnerDB(cfg.db_file)
        keys = db.find_all_api_keys()
        for key in keys:
            if request.headers.get('x-api-key') and request.headers.get('x-api-key') == key:
                return view_function(*args, **kwargs)
        abort(401)

    return decorated_function
