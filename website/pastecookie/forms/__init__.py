#-*-coding:utf-8-*-
import hashlib

from flask import g
from flask import request
from flask.ext import wtf

from wtforms import BooleanField
from wtforms import FileField
from wtforms import SelectField
from wtforms import TextField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms import ValidationError

from wtforms.validators import Required
from wtforms.validators import Length
from wtforms.validators import Email
from wtforms.validators import EqualTo

from pastecookie.models import *
from pastecookie.utils.functions import *

__all__ = ['RegisterForm', 'LoginForm', 'PasteForm',
           'CommentForm', 'UserInfoForm', 'PasswordForm',
           'ProfileForm']

class BaseForm(wtf.Form):
    pass

def email_unique(form, field):
    if len(User.query.filter_by(email=field.data).all()) > 0:
        raise ValidationError(u'这个邮件地址已经有人注册了.')

def nickname_unique(form, field):
    if len(User.query.filter_by(nickname=field.data).all()) > 0:
        raise ValidationError(u'这个邮件地址已经有人注册了.')

def paste_fields_check(form, field):
    if request.files:
        file = request.files['code_file']
        if not file and not form.content.data:
            raise ValidationError(u'贴代码的方式有两种：贴代码片段和上传代码文件，请至少选择一项')

def tags_check(form, field):
    if not field.data:
        return True
    if len(field.data.split(' ')) > 3:
        raise ValidationError(u'标签不能超过3个.')

def old_password_check(form, field):
    user = getUserObject()
    if user.password != hash_password(field.data):
        raise ValidationError(u'当前密码不正确')
    return True

class RegisterForm(BaseForm):
    nickname = TextField(u'昵称', [Required(message=u'请填一个你喜欢的昵称吧'), Length(min=2, max=12, message=u"昵称最少一个字符, 最多12个字符"), nickname_unique])
    email = TextField(u'邮件地址', [Email(message=u'请输入正确的email地址')])
    password = PasswordField(u'密码', [Length(min=6, max=12, message=u'密码长度在6-12个字符之间'),
        Required(message=u'请输入密码')])
    password_confirm = PasswordField(u'密码确认', [Required(message=u'请输入密码'),
        EqualTo('password', message=u'密码必须相同')])

class ProfileForm(BaseForm):
    nickname = TextField(u'昵称', [Required(message=u'请填一个你喜欢的昵称吧'), Length(min=2, max=12, message=u"昵称最少一个字符, 最多12个字符"), nickname_unique])
    email = TextField(u'邮件地址', [Email(message=u'请输入正确的email地址')])
    agreement = BooleanField(u'注册条款', [Required()])

class UserInfoForm(BaseForm):
    nickname = TextField(u'昵称', [Required(), Length(min=2, max=12, message=u"昵称最少一个字符, 最多12个字符")])
    motoo = TextField(u'签名', [Length(min=0, max=80)])
    introduction = TextAreaField(u'介绍', [Length(min=0, max=160)])

class LoginForm(BaseForm):
    email = TextField(u'邮件地址', [Required(), Length(min=6, max=30), Email()])
    password = PasswordField(u'密码', [Length(min=6, max=12), Required()])

class PasswordForm(BaseForm):
    old_password = PasswordField(u'当前密码', [Required(), old_password_check])
    new_password = PasswordField(u'新密码', [Required(), Length(min=6, max=12)])
    new_password_confirm = PasswordField(u'重复新密码', [Required(),
                    EqualTo('new_password', message=u'密码必须相同')])

class PasteForm(BaseForm):
    title = TextField(u'标题')
    syntax = SelectField(u'语法', choices=Syntax.get_syntax_list())
    content = TextAreaField(u'代码')
    tag = TextField(u'标签', [tags_check])
    description = TextAreaField(u'描述')
    code_file = FileField(u'文件', [paste_fields_check])
    is_private = BooleanField(u'Public')

class CommentForm(BaseForm):
    content = TextAreaField(u'评论', [Required(message=u"评论不能为空")])
