#-*-coding:utf-8-*-
import time
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask import session
from flask import render_template
from flask import g
from flask import abort
from flask import request

from flask.ext.babel import gettext
from flask.ext.themes import setup_themes
from flask.ext.themes import load_themes_from
from flask.ext.themes import theme_paths_loader

from pastecookie import render
from pastecookie.models import User

def config_app(app, db, oid, babel, config):
    app.config.from_pyfile(config)
    setup_themes(app, app_identifier="application")
    db.init_app(app)
    oid.init_app(app)
    babel.init_app(app)
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
        g.start_time = time.time()
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
            app.log.error(str(e))
            abort(500)
        return response

    @babel.localeselector
    def get_locale():
        user = getattr(g, 'user', None)
        if user:
            return getattr(user, 'locale', 'zh')
        return request.accept_languages.best_match(['en', 'zh'])

    @babel.timezoneselector
    def get_timezone():
        user = getattr(g, 'user', None)
        if user:
            return user.get('timezone', None)


def dispatch_handlers(app):
    d = {}
    @app.errorhandler(403)
    def permission_error(error):
        d['title'] = gettext('permission_denied_title')
        d['message'] = gettext('permission_denied_message')
        return render('error.html', **d), 403

    @app.errorhandler(404)
    def page_not_found(error):
        d['title'] = gettext('page_not_found_title')
        d['message'] = gettext('page_not_found_message')
        return render('error.html', **d), 404

    @app.errorhandler(500)
    def page_error(error):
        d['title'] = gettext('internal_error_title')
        d['message'] = gettext('internal_error_message')
        app.logger.error(str(error))
        return render('error.html', **d), 500


def dispatch_views(app):
    from pastecookie.views import pasteview
    from pastecookie.views import userview
    from pastecookie.views import rankview
    from pastecookie.views import tagview
    from pastecookie.views import adminview
    from pastecookie.views import siteview

    from pastecookie.utils.filters import dateformat
    from pastecookie.utils.filters import avatar
    from pastecookie.utils.filters import empty
    from pastecookie.utils.filters import time_passed
    from pastecookie.utils.filters import markdown

    app.jinja_env.filters['dateformat'] = dateformat
    app.jinja_env.filters['avatar'] = avatar
    app.jinja_env.filters['empty'] = empty
    app.jinja_env.filters['time_passed'] = time_passed
    app.jinja_env.filters['markdown'] = markdown
