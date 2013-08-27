#-*-coding:utf-8-*-
import time
from cStringIO import StringIO
from datetime import datetime

from flask import Blueprint
from flask import request
from flask import url_for
from flask import redirect
from flask import abort
from flask import send_file
from flask import g
from flask import session

from pygments import highlight
from pygments.lexers import find_lexer_class
from pygments.formatters import HtmlFormatter
from pygments.formatters import ImageFormatter
from pygments.formatters import NullFormatter

from daimaduan import app
from daimaduan import db
from daimaduan.models import *
#from daimaduan.forms import *
from daimaduan.utils.functions import *
from daimaduan.utils.decorators import *

PAGE_SIZE = app.config.get('PAGE_SIZE')

pasteview = Blueprint('pasteview', __name__)

def updateViewTimes(model, paste_id):
    paste_id = str(paste_id)
    if 'pastes' not in session:
        pastes = []
    else:
        pastes = session['pastes'].split(',')
    if paste_id in pastes:
        return True
    model.view_num = model.view_num + 1
    db.session.add(model)
    pastes.append(paste_id)
    session['pastes'] = ','.join(pastes)
    return True

@pasteview.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PasteForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        user = g.user
        paste = Paste(form.syntax.data,
                      user.id)
        file = request.files['code_file']
        if file:
            paste.content = file.stream.read()
        elif form.content.data:
            paste.content = form.content.data
        if form.title.data:
            paste.title = form.title.data
        if form.description.data:
            paste.description = form.description.data
        if form.is_private.data:
            paste.is_private = True
        user.paste_num = user.paste_num + 1
        paste.followers.append(user)
        db.session.add(user)
        db.session.add(paste)
        syntax_obj = Syntax.query.filter_by(id=form.syntax.data).first()
        tags = [syntax_obj.tag]
        if form.tag.data:
            tags.extend(form.tag.data.split())
        Tag.updateTags(paste, tags)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(500)
        if user.followers:
            mt = MessageTemplate.query.filter_by(used_for='create_paste').first()
            if mt:
                for to_user in user.followers:
                    message = Message(user.id,
                                      to_user.id,
                                      mt.title % user.nickname,
                                      mt.content % (user.nickname, paste.title, url_for('pasteview.view', paste_id=paste.id)))
                    db.session.add(message)
        mt = MessageTemplate.query.filter_by(used_for='create_paste_by_tag').first()
        if mt:
            for tag in paste.tags:
                for to_user in tag.followers:
                    if to_user.id != user.id:
                        message = Message(user.id,
                                          to_user.id,
                                          mt.title % tag.name,
                                          mt.content % (tag.name, paste.title, url_for('pasteview.view', paste_id=paste.id)))
                        db.session.add(message)
        try:
            db.session.commit()
        except Exception, e:
            app.log.error(str(e))
            abort(500)
        return redirect(url_for('pasteview.view', paste_id=paste.id))
    g.form = form
    return render_template('pasteview/create.html')

@pasteview.route('/edit/<paste_id>', methods=['GET', 'POST'])
@login_required
def edit(paste_id):
    model = Paste.query.get_or_404(paste_id)
    user = getUserObject()
    g.syntax = Syntax.get_syntax_list()
    if (model.user.id != user.id) and (not user.check_privilege(4)):
        abort(403)
    form = PasteForm(request.form, csrf_enabled=False)
    if request.method == 'GET':
        form.title.data = model.title
        form.content.data = model.content
        form.syntax.data = str(model.syntax_id)
        form.tag.data = ' '.join([tag.name for tag in model.tags])
    elif request.method == 'POST' and form.validate():
        model.title = form.title.data
        model.content = form.content.data
        if form.description.data:
            model.description = form.description.data
        syntax = Syntax.query.filter_by(id=form.syntax.data).first()
        model.syntax_id = syntax.id
        model.modified_time = datetime.now()
        if form.is_private.data:
            model.is_private = True
        tags = form.tag.data.strip().split()
        Tag.updateTags(model, set(tags))
        db.session.add(model)
        if user.followers:
            mt = MessageTemplate.query.filter_by(used_for='update_paste').first()
            if mt:
                for to_user in user.followers:
                    message = Message(user.id,
                                      to_user.id,
                                      mt.title % model.title,
                                      mt.content % (model.title, url_for('pasteview.view', paste_id=model.id)))
                    db.session.add(message)
        return redirect(url_for('pasteview.view', paste_id=model.id))
    g.model = model
    g.form = form
    #g.syntax = Syntax.get_syntax_list()
    return render_template('pasteview/edit.html')

@pasteview.route('/view/<paste_id>', methods=['GET', 'POST'])
def view(paste_id):
    model = Paste.query.get_or_404(paste_id)
    output = request.args.get('output', None)
    if output == 'raw':
        resp = make_response(model.content, 200)
        resp.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return resp
    user = getUserObject()
    form = CommentForm(request.form, csrf_enabled=False)
    if request.method == 'POST':
        if user:
            if form.validate():
                content, users = get_usernames_from_comment(form.content.data)
                comment = PasteComment(user.id, model.id, content)
                model.comment_num = model.comment_num + 1
                if user.id != model.user_id:
                    if user not in model.followers:
                        model.followers.append(user)
                db.session.add(comment)
                mt = MessageTemplate.query.filter_by(used_for='new_comment').first()
                if mt:
                    if model.followers:
                        for to_user in model.followers:
                            if to_user.id != user.id:
                                message = Message(user.id,
                                                  to_user.id,
                                                  mt.title % model.title,
                                                  mt.content % (model.title, url_for('pasteview.view', paste_id=paste_id)))
                                db.session.add(message)
                mt = MessageTemplate.query.filter_by(used_for='new_comment_has_user').first()
                if mt:
                    if users:
                        for to_user in users:
                            if to_user.id != user.id:
                                message = Message(user.id,
                                                  to_user.id,
                                                  mt.title,
                                                  mt.content % url_for('pasteview.view', paste_id=paste_id))
                                db.session.add(message)
                return redirect(url_for('pasteview.view', paste_id=paste_id))
    updateViewTimes(model, paste_id)
    lexer = find_lexer_class(model.syntax.name)
    formatter = HtmlFormatter(linenos='table', cssclass="source")
    g.code = highlight(model.content, lexer(stripall=True), formatter)
    g.model = model
    g.user = user
    g.form = form
    g.top_users = User.query.order_by('-paste_num')[:PAGE_SIZE]
    g.top_tags = Tag.query.order_by('-times')[:PAGE_SIZE]
    g.syntax_theme = request.args.get('css', app.config.get('DEFAULT_SYNTAX_CSS_FILE'))
    g.css_file = "/static/css/themes/%s.css" % g.syntax_theme
    #g.syntax_themes = SyntaxTheme.get_all_syntax_themes()
    return render_template('pasteview/view.html')

@pasteview.route('/delete/<paste_id>')
@login_required
def delete(paste_id):
    model = Paste.query.get_or_404(paste_id)
    user = getUserObject()
    if model.user.id != user.id:
        if not user.check_privilege(5):
            abort(403)
    user.paste_num = user.paste_num - 1
    if user.paste_num < 0:
        user.paste_num = 0
    db.session.add(user)
    model.is_delete = True
    db.session.add(model)
    return redirect('/')

@pasteview.route('/delete_comment/<comment_id>')
@login_required
def delete_comment(comment_id):
    model = PasteComment.query.get_or_404(comment_id)
    user = getUserObject()
    if model.user.id != user.id:
        if not user.check_privilege(5):
            abort(403)
    paste = Paste.query.get_or_404(model.paste_id)
    paste.comment_num = paste.comment_num - 1
    db.session.add(paste)
    db.session.delete(model)
    return redirect(url_for('pasteview.view', paste_id=paste.id))

@pasteview.route('/download/<paste_id>', methods=['POST'])
def download(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    filename = request.form.get('filename', None)
    if not filename:
        filename = "%s.txt" % paste.id
    fp = StringIO()
    fp.write(paste.content.encode('utf-8'))
    fp.seek(0)
    return send_file(fp, mimetype="text", as_attachment=True, attachment_filename=filename)

@pasteview.route('/favourite', methods=['POST'])
def favourite():
    paste_id = request.form.get('id', None)
    if paste_id:
        try:
            model = Paste.query.get_or_404(int(paste_id))
            user = getUserObject()
        except:
            model, user = None, None
        if model and user:
            if model not in user.favourites:
                user.favourites.append(model)
                db.session.add(user)
                return json.dumps({'result':'success', 'action':'add', 'message': u'收藏成功'})
            else:
                user.favourites.remove(model)
                db.session.add(user)
                return json.dumps({'result':'success', 'action':'del', 'message': u'取消收藏'})
    return json_response({'result':'fail', 'message': u'请先登陆!'})

@pasteview.route('/follow')
def follow():
    state = ''
    if 'user' not in session:
        return json_response({'result': 'fail', 'message': u'请先登陆!'})
    object_id = request.args.get('id', None)
    if object_id:
        paste = Paste.query.get_or_404(object_id)
        user = getUserObject()
        if user not in paste.followers:
            paste.followers.append(user)
            state = 'follow'
        else:
            paste.followers.remove(user)
            state = 'unfollow'
        db.session.add(paste)
        return json_response({'result': 'success', 'message': u'操作成功', 'state': state})


@pasteview.route('/favorite')
def favorite():
    state = ''
    if 'user' not in session:
        return json_response({'result': 'fail', 'message': u'请先登陆!'})
    object_id = request.args.get('id', None)
    if object_id:
        paste = Paste.query.get_or_404(object_id)
        user = getUserObject()
        if paste in user.favorites:
            user.favorites.remove(paste)
            state = 'unfavorite'
        else:
            user.favorites.append(paste)
            state = 'favorite'
        db.session.add(user)
        return json_response({'result': 'success', 'message': u'操作成功', 'state': state})


@pasteview.route('/rate/<object_id>', methods=['POST'])
def rate(object_id):
    if 'user' not in session:
        return json_response({'result': 'fail',
                           'message': u'请登陆再评价'})

    paste = Paste.query.get_or_404(object_id)
    user = g.user
    rate = PasteRate.query.filter_by(user_id=user.id, paste_id=paste.id).all()
    if rate:
        return json_response({'result': 'fail',
                           'message': u'已经评价过了, 不能再评价了'})
    number = request.form.get('number', None)
    if not number:
        return json_response({'result': 'fail',
                           'message': u'服务器出错啦, 一会再评价吧'})
    rate = PasteRate(user.id,
                     paste.id,
                     int(number))
    db.session.add(rate)
    rates = PasteRate.query.filter_by(paste_id=paste.id).all()
    if rates:
        total = 0
        for rate in rates:
            total = total + rate.rate
        paste.rate_num = total / len(rates)
    else:
        paste.rate_num = number
    db.session.add(paste)
    return json_response({'result': 'success',
                       'message': u'评价成功!',
                       'rate': paste.rate_num})
