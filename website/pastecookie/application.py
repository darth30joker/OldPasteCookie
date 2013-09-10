#-*-coding:utf-8-*-
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask import session
from flask import render_template
from flask import g
from flask import abort
from flask import request

from flask.ext.themes import setup_themes
from flask.ext.themes import load_themes_from
from flask.ext.themes import theme_paths_loader

from pastecookie import render

from pastecookie.models import User

def config_app(app, db, oid, config):
    app.config.from_pyfile(config)
    setup_themes(app, app_identifier="application")
    db.init_app(app)
    oid.init_app(app)
    formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    file_handler = RotatingFileHandler(app.config['ERROR_LOG'],
                                       maxBytes=100000,
                                       backupCount=0)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    @app.before_request
    def before_request():
        g.TITLE = app.config.get('TITLE')
        g.user = None
        if 'user' in session:
            g.user = User.query.filter_by(id=session['user']).first()
        g.url= request.url

    @app.after_request
    def after_request(response):
        try:
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            #app.log.error(str(e))
            print str(e)
            abort(500)
        return response

def dispatch_handlers(app):
    d = {}
    @app.errorhandler(403)
    def permission_error(error):
        d['title'] = u'您没有权限'
        d['message'] = u'您没有权限执行当前的操作, 请登陆或检查url是否错误.'
        return render('error.html', **d), 403

    @app.errorhandler(404)
    def page_not_found(error):
        d['title'] = u'页面不存在'
        d['message'] = u'您所访问的页面不存在, 是不是打错地址了啊?'
        return render('error.html', **d), 404

    @app.errorhandler(500)
    def page_error(error):
        d['title'] = u'页面出错啦'
        d['message'] = u'您所访问的页面出错啦! 待会再来吧!'
        app.logger.error(str(error))
        return render('error.html', **d), 500

def dispatch_views(app):
    from pastecookie.views import siteview
    from pastecookie.views import pasteview
    from pastecookie.views import userview
    from pastecookie.views import rankview
    from pastecookie.views import tagview
    from pastecookie.views import adminview

    app.register_blueprint(pasteview, url_prefix='/paste')
    app.register_blueprint(userview,  url_prefix='/user')
    app.register_blueprint(rankview,  url_prefix='/rank')
    app.register_blueprint(tagview,   url_prefix='/tag')
    app.register_blueprint(adminview, url_prefix='/admin')
    app.register_blueprint(siteview)

    from pastecookie.utils.filters import dateformat, avatar, empty, time_passed, markdown
    app.jinja_env.filters['dateformat'] = dateformat
    app.jinja_env.filters['avatar'] = avatar
    app.jinja_env.filters['empty'] = empty
    app.jinja_env.filters['time_passed'] = time_passed
    app.jinja_env.filters['markdown'] = markdown
