#-*-coding:utf-8-*-
import simplejson as json

from flask import Blueprint
from flask import request
from flask import g
from flask import url_for
from flask import redirect

from daimaduan import app
from daimaduan import render
#from daimaduan.forms import *
from daimaduan.models import *

PAGE_SIZE = app.config.get('PAGE_SIZE')
SIDEBAR_PAGE_SIZE = app.config.get('SIDEBAR_PAGE_SIZE')

rankview = Blueprint('rankview', __name__)

@rankview.route('/', methods=['GET'])
def rank():
    g.top_tags = Tag.query.order_by('times DESC')[:SIDEBAR_PAGE_SIZE]
    g.top_view_pastes = Paste.query.filter_by(is_private=False).filter_by(is_delete=False).order_by('view_num DESC')[:SIDEBAR_PAGE_SIZE]
    g.top_comment_pastes = Paste.query.filter_by(is_private=False).order_by('comment_num DESC')[:SIDEBAR_PAGE_SIZE]
    g.users = User.query.order_by('paste_num DESC')[:SIDEBAR_PAGE_SIZE]
    return render('rankview/rank.html')
