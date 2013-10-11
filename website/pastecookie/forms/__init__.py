#-*-coding:utf-8-*-
import hashlib

from flask import g
from flask import request
from flask.ext import wtf
from flask.ext.babel import gettext

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
        raise ValidationError(gettext('email_is_taken'))

def nickname_unique(form, field):
    if len(User.query.filter_by(nickname=field.data).all()) > 0:
        raise ValidationError(gettext('nickname_is_taken'))

def paste_fields_check(form, field):
    if request.files:
        file = request.files['code_file']
        if not file and not form.content.data:
            raise ValidationError(gettext('paste_your_code_or_select_a_file'))

def tags_check(form, field):
    if not field.data:
        return True
    if len(field.data.split(' ')) > 3:
        raise ValidationError(gettext('no_more_than_3_tags'))

def old_password_check(form, field):
    user = getUserObject()
    if user.password != hash_password(field.data):
        raise ValidationError(gettext('password_not_correct'))
    return True

class RegisterForm(BaseForm):
    nickname = TextField(gettext('nickname'),
        [Required(message=gettext('nickname_is_required')),
         Length(min=2, max=12, 
                message=gettext('nickname_more_than_2_letters_less_than_12_letters')),
         nickname_unique])
    email = TextField(gettext('email'), [Email(message=gettext('email_not_correct'))])
    password = PasswordField(gettext('password'),
        [Length(min=6, max=12, message=gettext('password_more_than_6_letters_less_than_12_letters')),
         Required(message=gettext('password_is_required'))])
    password_confirm = PasswordField(gettext('password_confirmation'), [Required(message=gettext('password_confirmation_is_required')),
        EqualTo('password', message=gettext('password_not_equal'))])

class ProfileForm(BaseForm):
    nickname = TextField(gettext('nickname'),
        [Required(message=gettext('nickname_is_required')),
         Length(min=2, max=12,
                message=gettext('nickname_more_than_2_letters_less_than_12_letters')),
         nickname_unique])
    email = TextField(gettext('email'), [Email(message=gettext('email_not_correct'))])

class UserInfoForm(BaseForm):
    nickname = TextField(gettext('nickname'),
        [Required(),
         Length(min=2, max=12,
                message=gettext('nickname_more_than_2_letters_less_than_12_letters'))])
    motoo = TextField(gettext('motoo'), [Length(min=0, max=80)])
    introduction = TextAreaField(gettext('introduction'), [Length(min=0, max=160)])

class LoginForm(BaseForm):
    email = TextField(gettext('email'), [Required(), Length(min=6, max=30), Email()])
    password = PasswordField(gettext('password'), [Length(min=6, max=12), Required()])

class PasswordForm(BaseForm):
    old_password = PasswordField(gettext('old_password'), [Required(), old_password_check])
    new_password = PasswordField(gettext('new_password'), [Required(), Length(min=6, max=12)])
    new_password_confirm = PasswordField(gettext('new_password_confirm'),
        [Required(),
         EqualTo('new_password', message=gettext('password_not_equal'))])

class PasteForm(BaseForm):
    title = TextField(gettext('paste_title'))
    syntax = SelectField(gettext('paste_syntax'), choices=Syntax.get_syntax_list)
    content = TextAreaField(gettext('paste_code'))
    tag = TextField(gettext('paste_tags'), [tags_check])
    description = TextAreaField(gettext('paste_description'))
    code_file = FileField(gettext('paste_file'), [paste_fields_check])
    is_private = BooleanField(gettext('paste_is_private'))

class CommentForm(BaseForm):
    content = TextAreaField(gettext('comment'),
        [Required(message=gettext('comment_is_required'))])
