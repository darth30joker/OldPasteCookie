#!/usr/bin/env python
#-*-coding:utf-8-*-
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask.ext.script import Manager

from pastecookie import app
from pastecookie import db
from pastecookie import oid

from pastecookie.application import config_app
from pastecookie.application import dispatch_handlers
from pastecookie.application import dispatch_views


CURRENT_PATH = os.path.abspath(__file__)

manager = Manager(app, with_default_commands=False)


def get_config_file_path(config):
    return os.path.abspath(config)


@manager.option('-c', '--config', dest='config', help='Configuration file name')
def run(config):
    config_app(app, db, oid, get_config_file_path(config))
    dispatch_handlers(app)
    dispatch_views(app)
    app.run(host='0.0.0.0')


@manager.option('-c', '--config', dest='config', help='Configuration file name')
def initdb(config):
    config_app(app, db, oid, get_config_file_path(config))
    db.init_app(app)

    print "Drop all tables"
    db.drop_all()

    print "Create all tables"
    db.create_all()

    print "Start to add all syntax"
    from pastecookie.models import Syntax, MessageTemplate, Page
    from pastecookie.models.syntax import ALL_SYNTAX
    for lexer in ALL_SYNTAX:
        syntax = Syntax(lexer[0], lexer[1].lower())
        db.session.add(syntax)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    from pastecookie.models.data import pages, templates
    for page in pages:
        new_page = Page(page['slug'],
                        page['title'],
                        page['content'])
        db.session.add(new_page)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    for template in templates:
        new_temp = MessageTemplate(template['used_for'],
                                   template['title'],
                                   template['content'])
        db.session.add(new_temp)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    try:
        db.session.execute("select setval(pg_get_serial_sequence('users', 'id'), 999);")
        db.session.execute("select setval(pg_get_serial_sequence('pastes', 'id'), 999);")
        db.session.commit()
    except:
        pass


@manager.option('-c', '--config', dest='config', help='Configuration file name')
def generate_test(config):
    config_app(app, get_config_file_path(config))

    from pastecookie.models import User, UserInfo, Syntax, Tag, Paste
    user1 = User('davidx', 'david.xie@me.com')
    user1.set_password('123456')
    info1 = UserInfo(user1.id)
    user1.info = info1
    db.session.add(user1)

    user2 = User('zhangkai', 'zhangkai@pastecookie.com')
    user2.set_password('123456')
    info2 = UserInfo(user2.id)
    user2.info = info2
    db.session.add(user2)

    user3 = User('guest', 'guest@pastecookie.com')
    user3.set_password('123456')
    info3 = UserInfo(user3.id)
    user3.info = info3
    db.session.add(user3)

    try:
        db.session.commit()
    except:
        db.session.rollback()

    db.session.add(info1)
    db.session.add(info2)
    db.session.add(info3)

    try:
        db.session.commit()
    except:
        db.session.rollback()

    users = [user1, user2, user3]

    from tests import FILES
    import random
    for filename, syntax, tags in FILES:
        syntax = Syntax.query.filter_by(name=syntax).first()
        f = open('tests/%s' % filename, 'r')
        paste = Paste(syntax.id,
                      users[random.randint(0, 2)].id)
        paste.title = filename
        paste.content = f.read()
        db.session.add(paste)

        for tag in tags:
            t = Tag.query.filter_by(name=tag).first()
            if not t:
                t = Tag(tag)
                db.session.add(t)
            paste.tags.append(t)
        db.session.add(paste)
        f.close()

        try:
            db.session.commit()
        except Exception, e:
            print str(e)
            db.session.rollback()


@manager.option('-c', '--config', dest='config', help='Configuration file name')
@manager.option('-e', '--email', dest='email', help='Email address')
@manager.option('-p', '--privilege', dest='privilege', help='Privilege number')
def privilege(config, email, privilege):
    config_app(app, get_config_file_path(config))
    db.init_app(app)

    from pastecookie.models import User

    user = User.query.filter_by(email=email).first()
    if not user:
        print "User can not be found."
    else:
        user.privilege = int(privilege)
        db.session.add(user)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            print "error"
        print "Modification successed."


@manager.option('-c', '--config', dest='config', help='Configuration file name')
def add_syntax(config):
    config_app(app, get_config_file_path(config))
    db.init_app(app)
    db.create_all()

    from pastecookie.models import SyntaxTheme

    path = 'pastecookie/static/css/themes'
    for f in os.listdir(path):
        if os.path.isfile("%s/%s" % (path, f)):
            if f.endswith('css'):
                name = f.split('.')
                st = SyntaxTheme(name[0], f)
                db.session.add(st)
    db.session.commit()


if __name__ == '__main__':
    manager.run()
