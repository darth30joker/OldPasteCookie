#-*-coding:utf-8-*-
from flask import Flask
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='../static', template_folder='../templates')
db = SQLAlchemy(app)
oid = OpenID()
