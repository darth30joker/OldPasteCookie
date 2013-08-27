#-*-coding:utf-8-*-
from site import site_blueprint
from paste import paste_blueprint
from user import user_blueprint
from tag import tag_blueprint
from rank import rank_blueprint
from admin import admin_blueprint

__all__ = ['site_blueprint', 'paste_blueprint', 'user_blueprint',
           'tag_blueprint', 'rank_blueprint', 'admin_blueprint']
