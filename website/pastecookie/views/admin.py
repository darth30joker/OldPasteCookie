#-*-coding:utf-8-*-
import time
import simplejson as json

from datetime import datetime

from flask import Blueprint
from flask import abort
from flask import g
from flask import make_response
from flask import redirect
from flask import request
from flask import url_for

from pastecookie import app
from pastecookie import db
from pastecookie.models import *
#from pastecookie.forms import *
from pastecookie.utils.functions import *
from pastecookie.utils.decorators import *

adminview = Blueprint('adminview', __name__)

PAGE_SIZE = app.config.get('PAGE_SIZE')

@adminview.before_request
def before_request():
    if 'user' not in session:
        return redirect(url_for('userapp.login'))
    g.user = getUserObject()
    if g.user:
        if not g.user.check_privilege(5):
            return redirect(url_for('userapp.login'))
    else:
        return redirect(url_for('userapp.login'))

@adminview.after_request
def after_request(response):
    try:
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        #app.log.error(str(e))
        abort(500)
    return response

@adminview.route('/')
def index():
    return render_template('adminview/index.html')

@adminview.route('/users')
def users():
    if request.method == 'POST':
        nickname = request.form.get('nickname', None)
        email = request.form.get('email', None)
    page = request.args.get('page', 1)
    g.users = User.query.all()
    return render_template('adminview/users.html')

@adminview.route('/tags', methods=['GET', 'POST'])
def tags():
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1
    delete = request.args.get('delete', None)
    object_id = request.args.get('object_id', None)
    if delete and object_id:
        if delete == 'true':
            tag = Tag.query.get_or_404(object_id)
            if tag:
                db.session.delete(tag)
                return redirect('%s?page=%s' % (url_for('adminview.tags'), page))
    if request.method == 'POST':
        object_id = request.form.get('object_id', None)
        name = request.form.get('name', None)
        description = request.form.get('description', None)
        if object_id:
            tag = Tag.query.get_or_404(object_id)
            if tag:
                tag.name = name
                tag.description = description
                db.session.add(tag)
                data = {'result':'success'}
            else:
                data = {'result':'fail', 'message':u'没有该页面'}
            """
            resp = make_response(json.dumps(data), 200)
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            """
            return redirect("%s?page=%s" % (url_for('adminview.tags'), page))
    g.paginate = Tag.query.order_by('name').paginate(page, PAGE_SIZE)
    return render_template('adminview/tags.html')

@adminview.route('/pastes')
def pastes():
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1
    g.paginate = Paste.query.paginate(page, PAGE_SIZE)
    return render_template('adminview/pastes.html')

@adminview.route('/pages', methods=['GET', 'POST'])
def pages():
    if request.method == 'POST':
        page_id = request.form.get('object_id', None)
        title = request.form.get('title', None)
        slug = request.form.get('slug', None)
        content = request.form.get('content', None)
        if page_id:
            page = Page.query.filter_by(id=page_id).first()
            if page:
                page.title = title
                page.content = content
                page.slug = slug
                page.modified_time = datetime.now()
                db.session.add(page)
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                    abort(500)
                data = {'result':'success'}
            else:
                data = {'result':'fail', 'message':u'没有该页面'}
            return redirect(url_for('adminview.pages'))
        else:
            page = Page(slug, title, content)
            db.session.add(page)
            return redirect(url_for('adminview.pages'))
    if request.args.get('object_id', None) and request.args.get('delete', None) == 'True':
        page = Page.query.filter_by(id=request.args.get('object_id', None)).first()
        if page:
            db.session.delete(page)
        return redirect(url_for('adminview.pages'))
    g.pages = Page.query.all()
    return render_template('adminview/pages.html')

@adminview.route('/message_template', methods=['GET', 'POST'])
def message_template():
    if request.method == 'POST':
        mt_id = request.form.get('object_id', None)
        title = request.form.get('title', None)
        used_for = request.form.get('used_for', None)
        content = request.form.get('content', None)
        if mt_id:
            mt = MessageTemplate.query.filter_by(id=mt_id).first()
            if mt:
                mt.title = title
                mt.content = content
                mt.used_for = used_for
                mt.modified_time = datetime.now()
                db.session.add(mt)
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                    abort(500)
                data = {'result':'success'}
            else:
                data = {'result':'fail', 'message':u'没有该页面'}
            return redirect(url_for('adminview.message_template'))
        else:
            mt = MessageTemplate(used_for, title, content)
            db.session.add(mt)
            return redirect(url_for('adminview.message_template'))
    if request.args.get('object_id', None) and request.args.get('delete', None) == 'True':
        mt = MessageTemplate.query.filter_by(id=request.args.get('object_id', None)).first()
        if mt:
            db.session.delete(mt)
        return redirect(url_for('adminview.message_template'))
    g.models = MessageTemplate.query.all()
    return render_template('adminview/message_template.html')


@adminview.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'POST':
        post_id = request.form.get('object_id', None)
        title = request.form.get('title', None)
        content = request.form.get('content', None)
        if post_id:
            post = Post.query.get_or_404(id=post_id)
            post.title = title
            post.content = content
            post.modified_time = datetime.now()
            db.session.add(post)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                abort(500)
            return redirect(url_for('adminview.posts'))
        else:
            post = Post(title, content)
            db.session.add(post)
            return redirect(url_for('adminview.posts'))
    if request.args.get('object_id', None) and request.args.get('delete', None) == 'True':
        post = Post.query.filter_by(id=request.args.get('object_id', None)).first()
        if post:
            db.session.delete(post)
        return redirect(url_for('adminview.posts'))
    g.posts = Post.query.all()
    return render_template('adminview/posts.html')

app.register_blueprint(adminview, url_prefix='/admin')
