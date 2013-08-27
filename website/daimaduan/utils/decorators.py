#-*-coding:utf-8-*-
from flask import request, session, url_for, redirect, abort, send_file, g
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            return redirect(url_for('userapp.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
