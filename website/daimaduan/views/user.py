#-*-coding:utf-8-*-
import hashlib, time
import simplejson as json

from datetime import datetime

from flask import Blueprint
from flask import request
from flask import url_for
from flask import redirect
from flask import abort
from flask import flash
from flask import g

from flask.ext.openid import COMMON_PROVIDERS

from daimaduan import db
from daimaduan import oid

#from daimaduan.forms import *
from daimaduan.models import *
from daimaduan.utils.functions import *
from daimaduan.utils.decorators import *

userview = Blueprint('userview', __name__)

@userview.route('/login/', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST':
        openid = request.form.get('openid', None)
        if openid:
            return oid.try_login(COMMON_PROVIDERS.get(openid, "google"),
                                 ask_for=['email', 'nickname'])
        if form.validate():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                if user.password == hashPassword(form.password.data):
                    user.last_login_time = datetime.now()
                    session['user'] = str(user.id)
                    flash(u'成功登入', 'success')
                    return redirect(request.args.get('next', '/'))
                else:
                    flash(u'用户名/密码错误', 'error')
    g.form = form
    return render_template('userview/login.html',
                           next=oid.get_next_url(),
                           error=oid.fetch_error())

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'成功登入', 'success')
        session['user'] = str(user.id)
        session.pop('openid')
        g.user = getUserObject(user_id=session['user'])
        g.user.last_login_time = datetime.now()
        return redirect(request.args.get('next', '/'))
    return redirect(url_for('userview.create_profile',
                            next=oid.get_next_url(),
                            nickname=resp.nickname,
                            email=resp.email))

@userview.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    form = ProfileForm(request.form)
    form.nickname.data = request.values.get('nickname')
    form.email.data = request.values.get('email')
    if request.method == 'POST' and form.validate():
        user = User(form.nickname.data,
                    form.email.data)
        user.openid = session['openid']
        info = UserInfo(user.id)
        user.info = info
        db.session.add(user)
        db.session.add(info)
        db.session.commit()
        flash(u'资料建立成功', 'success')
        session.pop('openid')
        session['user'] = user.id
        return redirect("/")
    g.form = form
    return render_template('userview/create_profile.html', next_url=oid.get_next_url())

@userview.route('/logout', methods=['GET'])
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect('/')

@userview.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form, csrf_enabled=False)
    g.form = form
    if 'user' in session:
        flash(u'请先登出再注册新用户', 'error')
        return render_template('userview/register.html')
    if request.method == 'POST' and form.validate():
        user = User(form.nickname.data,
                    form.email.data)
        user.set_password(form.password.data)
        info = UserInfo(user.id)
        user.info = info
        db.session.add(user)
        db.session.add(info)
        try:
            db.session.commit()
        except Exception, e:
            abort(500)
        flash(u'注册成功!', 'success')
        return redirect(url_for('userview.login'))
    flash(u'如果您有google帐号, 可以直接使用google提供的openid方式登录, 请点击登录按钮然后选择google帐号登录', 'alert')
    return render_template('userview/register.html')

@userview.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    form = UserInfoForm(request.form, csrf_enabled=False)
    user = getUserObject()
    if request.method == 'POST' and form.validate():
        user.nickname = form.nickname.data
        user.info.motoo = form.motoo.data
        user.info.introduction = form.introduction.data
        db.session.add(user)
        flash(u'信息修改成功', 'success')
        return redirect(url_for('userview.manage'))
    if request.method == 'GET':
        form.motoo.data = user.info.motoo
        form.introduction.data = user.info.introduction
        form.nickname.data = user.nickname
    if form.errors:
        for error in form.errors:
            flash(form.errors[error][0], 'error')
    g.form = form
    return render_template('userview/manage.html')

@userview.route('/password', methods=['GET', 'POST'])
@login_required
def password():
    form = PasswordForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        user = getUserObject()
        user.password = hashPassword(form.new_password.data)
        db.session.add(user)
        flash(u'密码修改成功', 'success')
        redirect(url_for('userview.logout'))
    g.form = form
    return render_template('userview/password.html')

@userview.route('/<slug>', methods=['GET'])
@userview.route('/view/<user_id>', methods=['GET'])
def view(user_id=None, slug=None):
    if slug:
        model = getUserObject(slug=slug)
    elif user_id:
        model = getUserObject(user_id=user_id)
    if model:
        g.model = model
        return render_template('userview/view.html')
    abort(404)

@userview.route('/openid', methods=['GET', 'POST'])
@login_required
def openid():
    """
    这个函数用来更换OpenID
    """
    if request.method == "POST":
        return oid.try_login(COMMON_PROVIDERS.get(openid, "google"),
                                 ask_for=['email', 'nickname'])
    return render_template('userview/openid.html')

@userview.route('/getuserinfo', methods=['POST'])
def getuserinfo():
    user_id = request.form.get('user_id', None)
    if not user_id:
        return json.dumps({'status': 'fail',
                           'message': u'Server Error'})
    user = getUserObject(user_id=user_id)
    return json.dumps({'status': 'success',
                       'data': {'id': user.id,
                                'avatar': user.avatar,
                                'paste_num': user.paste_num,
                                'nickname': user.nickname}
                     })

@userview.route('/follow')
def follow():
    state = ''
    if 'user' not in session:
        return json_response({'result': 'fail', 'message': u'请先登陆!'})
    object_id = request.args.get('id', None)
    if object_id:
        model = User.query.get_or_404(object_id)
        user = getUserObject()
        if model.id == user.id:
            return json_response({'result': 'fail', 'message': u'自己不能关注自己'})
        if user not in model.followers:
            model.followers.append(user)
            state = 'follow'
        else:
            model.followers.remove(user)
            state = 'unfollow'
        db.session.add(model)
        return json_response({'result':'success', 'state': state})

@userview.route('/<user_id>/rss.xml')
def rss(user_id):
    g.user = User.query.get_or_404(user_id)
    g.pastes = Paste.query.filter_by(user_id=user_id, is_private=False).order_by("created_time DESC").all()
    return render_template('rss/user.xml')

