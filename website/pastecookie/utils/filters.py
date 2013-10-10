#-*-coding:utf-8-*-
import hashlib
import re

from datetime import datetime
from markdown import markdown as mk

from flask.ext.babel import gettext

def dateformat(value, format="%Y-%m-%d %H:%M"):
    return value.strftime(format)

def empty(value, text=None):
    if not value:
        if text:
            return text
    return value

def time_passed(value):
    now = datetime.now()
    past = now - value
    if past.days:
        return gettext('%(days)s days ago', days=past.days)
    mins = past.seconds / 60
    if mins < 60:
        return gettext('%(minutes)s minutes ago', minutes=mins)
    hours = mins / 60
    return gettext('%(hours)s hours ago', hours=hours)

def markdown(value):
    return mk(value)

def avatar(value):
    return "http://www.gravatar.com/avatar/%s?size=120" % hashlib.md5(value).hexdigest()
