#-*-coding:utf-8-*-
import simplejson as json

from flask import Blueprint
from flask import request
from flask import g
from flask import redirect
from flask import render_template
from flask import abort

from daimaduan import app
from daimaduan import db

#from daimaduan.forms import *
from daimaduan.models import *

from daimaduan.utils.filters import *
from daimaduan.utils.decorators import *
from daimaduan.utils.functions import *

PAGE_SIZE = app.config['PAGE_SIZE']
SIDEBAR_PAGE_SIZE = app.config.get('SIDEBAR_PAGE_SIZE')

tag_blueprint = Blueprint('tag_blueprint', __name__)

@tag_blueprint.route('/list', methods=['GET'])
def list():
    g.users = User.query.order_by('paste_num DESC')[:SIDEBAR_PAGE_SIZE]
    g.tags = Tag.query.order_by('name').all()
    g.top_tags = Tag.query.order_by('-times')[:PAGE_SIZE]
    return render_template('tag_blueprint/list.html')

@tag_blueprint.route('/<tag_name>', methods=['GET'])
def view(tag_name):
    """
    """
    model = Tag.query.filter_by(name=tag_name).first_or_404()
    g.model = model
    g.pastes = Paste.query.join(Paste.tags).filter(Paste.tags.contains(g.model)).filter(Paste.is_private==False).order_by('pastes.created_time DESC').paginate(1, PAGE_SIZE)
    g.top_tags = Tag.query.order_by('times DESC').all()
    g.users = User.query.order_by("paste_num DESC").all()[:SIDEBAR_PAGE_SIZE]
    return render_template('tag_blueprint/view.html')

@tag_blueprint.route('/getmore', methods=['POST'])
def getmore():
    model = Tag.query.get_or_404(request.form.get('id', None))
    try:
        page = int(request.form.get('page', 1))
    except:
        return json_response({'result':'fail'})
    pagination = Paste.query.join(Paste.tags).filter(Paste.tags.contains(model)).order_by('pastes.created_time DESC').paginate(page, PAGE_SIZE)
    if pagination.pages <= page:
        return json_response({'result':'fail'})
    return json_response({'result':'success',
        'pastes':[
            {'view_num':paste.view_num, 'title':paste.title,
                'url':url_for('pasteapp.view', paste_id=paste.id), 'comment_num':len(paste.comments),
                'created_time':time_passed(paste.created_time),
                'user':{
                    'url':paste.user.url, 'nickname':paste.user.nickname,
                },
                'tags':[
                    {'id':tag.id, 'name':tag.name, 'url':url_for('tag_blueprint.view', tag_name=tag.name)}
                for tag in paste.tags]
            }
        for paste in pagination.items]})

@tag_blueprint.route('/follow', methods=['POST'])
def follow():
    if 'user' not in session:
        return json_response({'result':'fail', 'message': u'请先登录'})
    state = ''
    object_id = request.form.get('id', None)
    if object_id:
        tag = Tag.query.get_or_404(object_id)
        user = getUserObject()
        if user not in tag.followers:
            tag.followers.append(user)
            state = 'follow'
        else:
            tag.followers.remove(user)
            state = 'unfollow'
        db.session.add(tag)
        return json_response({'result':'success', 'message':u'关注成功', 'state':state})
    return json_response({'result':'fail', 'message':u'服务器错误, 请稍后再试'})

@tag_blueprint.route('/<tag>/rss.xml')
def rss(tag):
    g.tag = Tag.query.filter_by(name=tag).first()
    if not g.tag:
        abort(404)
    g.pastes = Paste.query.filter(Paste.tags.contains(g.tag)).filter_by(is_private=False).order_by("created_time DESC").all()
    return render_template('rss/tag.xml')
