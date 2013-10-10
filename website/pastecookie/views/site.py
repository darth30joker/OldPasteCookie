#-*-coding:utf-8-*-
import time

from flask import Blueprint
from flask import request
from flask import url_for
from flask import current_app
from flask import make_response
from flask import redirect
from flask import abort
from flask import send_file
from flask import g

from pastecookie import app
from pastecookie import db
from pastecookie import render

from pastecookie.models import *
from pastecookie.utils.decorators import login_required
from pastecookie.utils.filters import time_passed
from pastecookie.utils.functions import *

PAGE_SIZE = app.config.get('PAGE_SIZE')
SIDEBAR_TAG_PAGE_SIZE = app.config.get('SIDEBAR_TAG_PAGE_SIZE')
SIDEBAR_USER_PAGE_SIZE = app.config.get('SIDEBAR_USER_PAGE_SIZE')

siteview = Blueprint('siteview', __name__)


@siteview.route('/')
def index():
    g.new_pastes = Paste.query.filter_by(is_private=False).filter_by(is_delete=False).order_by('created_time DESC')[:PAGE_SIZE]
    g.top_tags = Tag.query.order_by('times DESC')[:SIDEBAR_TAG_PAGE_SIZE]
    g.users = User.query.order_by('created_time DESC')[:SIDEBAR_USER_PAGE_SIZE]
    return render('siteview/index.html')


@siteview.route('/page/<slug>')
def page(slug=None):
    if not slug:
        abort(404)
    g.page = Page.query.filter_by(slug=slug).first_or_404()
    return render('siteview/page.html')


@siteview.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    if keyword:
        g.users = User.query.filter(User.nickname.like("%" + keyword + "%"))
        g.pastes = Paste.query.filter(Paste.title.like("%" + keyword + "%"))
        g.tags = Tag.query.filter(Tag.name.like("%" + keyword + "%"))
        g.keyword = keyword
    g.top_tags = Tag.query.order_by('times DESC')[:SIDEBAR_TAG_PAGE_SIZE]
    g.top_users = User.query.order_by('paste_num DESC')[:SIDEBAR_USER_PAGE_SIZE]
    return render('siteview/search.html')


@siteview.route('/getmore', methods=['POST'])
def getmore():
    try:
        page = int(request.form.get('page', 1))
    except:
        return json_response({'result': 'fail'})
    pagination = Paste.query.filter_by(is_private=False).filter_by(is_delete=False).order_by('created_time DESC').paginate(page, PAGE_SIZE)
    if page > pagination.pages:
        return json_response({'result': 'fail'})
    return json_response({'result': 'success',
                          'pastes': [{
                                'id':paste.id,
                                'title':paste.title,
                                'view_num':paste.view_num,
                                'comment_num':len(paste.comments),
                                'url':url_for('pasteapp.view', paste_id=paste.id),
                                'created_time':time_passed(paste.created_time),
                                'desc':paste.description or '',
                                'user_nickname':paste.user.nickname,
                                'user_url':url_for('userapp.view', user_id=paste.user.id),
                                'is_user_followed':paste.is_user_followed and "true" or "false",
                                'is_user_favorited':paste.is_user_favorited and "true" or "false",
                                'tags':[{
                                    'name':tag.name,
                                    'url':url_for('tagapp.view', tag_name=tag.name)
                                    } for tag in paste.tags]
                          } for paste in pagination.items]})


@login_required
@siteview.route('/messages')
def messages():
    g.model = g.user
    g.messages = Message.query.filter_by(to_user_id=g.user.id).order_by("created_time DESC").all()
    return render('siteview/messages.html')


@login_required
@siteview.route('/read_message', methods=['POST'])
def read_message():
    object_id = request.form.get('object_id', None)
    if object_id:
        message = Message.query.get_or_404(object_id)
        if message:
            db.session.delete(message)
    return json_response({'result': 'success'})


@siteview.route('/posts')
def posts():
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1
    g.pagination = Post.query.order_by("created_time DESC").paginate(page, 10)
    return render('siteview/posts.html')

@siteview.route('/post/<object_id>')
def post(object_id=None):
    if not object_id:
        abort(404)
    g.post = Post.query.get_or_404(object_id)
    return render('siteview/post.html')

@siteview.route("/test")
def test():
    send_mail_to_queue(from_user="mykingheaven@gmail.com",
                       to_user="david.xie@me.com",
                       title=u"来试试中文",
                       content=u"打断的中文熬撒旦噶速度过来说的话过来撒很给力")
    return "hello!"

@siteview.route('/rss.xml')
def rss():
    g.pastes = Paste.query.filter_by(is_private=False).order_by("created_time DESC").all()
    return render('rss/site.xml')

app.register_blueprint(siteview)
