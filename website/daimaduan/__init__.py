#-*-coding:utf-8-*-
from flask import Flask
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.themes import render_theme_template

app = Flask(__name__, static_folder='../static', template_folder='../templates')
db = SQLAlchemy(app)
oid = OpenID()

def render(template, **kwargs):
    theme = app.config['THEME']
    return render_theme_template(theme, template, **kwargs)
