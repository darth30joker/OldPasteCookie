#-*-coding:utf-8-*-
import time
import hashlib
from datetime import datetime

from flask import g
from flask import url_for
from flask import request
from flask import session

from daimaduan import db
from daimaduan.utils.functions import hash_password

__all__ = ['User', 'Syntax', 'Paste', 'Tag', 'PasteComment', 'UserInfo',
           'Message', 'PasteRate', 'Page', 'MessageTemplate', 'getUserObject',
           #'SyntaxTheme'
           'Post'
           ]

def strip_tag(tag):
    return tag.strip("'\", ").replace(",", "").replace("_", "-")

def getUserObject(slug=None, user_id=None):
    user = None
    if not slug and not user_id:
        if 'user' in session:
            user = g.user
    elif slug:
        user = User.query.filter_by(slug=slug).first()
    elif user_id:
        user = User.query.filter_by(id=user_id).first()
    return user

# 这个表存储用户之间的关联
follow_user_user = db.Table('follow_user_user',
            db.Column('from_user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
            db.Column('to_user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
        )

# 这个表存储代码拥有的标签
paste_tag = db.Table('pastes_tags',
            db.Column('paste_id', db.Integer, db.ForeignKey('pastes.id')),
            db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
        )

# 这个表存储用户的收藏
favorite_paste_user = db.Table('favorite_paste_user',
             db.Column('user_id',  db.Integer, db.ForeignKey('users.id')),
             db.Column('paste_id', db.Integer, db.ForeignKey('pastes.id')),
        )

# 这个表存储用户与代码间的关注
follow_user_paste = db.Table('follow_user_paste',
             db.Column('user_id',  db.Integer, db.ForeignKey('users.id')),
             db.Column('paste_id', db.Integer, db.ForeignKey('pastes.id')),
        )

# 这个表存储用户与标签间的关注
follow_user_tag = db.Table('follow_user_tag',
             db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
             db.Column('tag_id',  db.Integer, db.ForeignKey('tags.id')),
        )

class Syntax(db.Model):
    """语法表"""
    __tablename__ = 'syntax'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), unique=True, nullable=False) # 显示的名字
    tag = db.Column(db.String(45), nullable=False) # 给tag用的, 用户不能改

    def __init__(self, name, tag):
        self.name = name
        self.tag = tag

    def __repr__(self):
        return "<Syntax (%s|%s)>" % (self.name, self.tag)

    @classmethod
    def get_syntax_list(self):
        all_syntax = Syntax.query.order_by('name').all()
        return [(str(one.id), one.name) for one in all_syntax]

"""
class SyntaxTheme(db.Model):
    __tablename__ = 'syntax_themes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), unique=True)
    css_file = db.Column(db.String(45), unique=True)

    def __init__(self, name, css_file):
        self.name = name
        self.css_file = css_file

    def __repr__(self):
        return "<SyntaxTheme (%s|%s)>" % (self.name, self.css_file)

    @classmethod
    def get_all_syntax_themes(self):
        syntax_themes = SyntaxTheme.query.order_by("name").all()
        return [one.name for one in syntax_themes]
"""

class Tag(db.Model):
    """
    标签表
    要求:
    1. 以小写存储
    2. 空格要替换成为'-'
    3. '和"都去掉
    """
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    times = db.Column(db.Integer)
    created_time = db.Column(db.DateTime, default=datetime.now())
    modified_time = db.Column(db.DateTime, default=datetime.now())

    followers = db.relationship('User', secondary=follow_user_tag)

    def __init__(self, name):
        self.name = name.replace(' ', '-').replace('"', '').replace("'", '')
        self.times = 1

    def __repr__(self):
        return "Tag <%s>" % self.name

    @classmethod
    def getTags(self, num):
        tags = Tag.query.all()[:num]
        return [tag.name for tag in tags]

    def is_focused(self):
        return getUserObject() in self.followers

    @classmethod
    def updateTags(self, model, tags=[]):
        """
        model: 要创建tag的model
        tags: 页面传过来的tag, list形式
        这里的逻辑有些复杂, 有必要写一个详细的注释
        准则:
        1. 检查tag是否超过3个
        2. 不管什么大小写, 不能有重复的
        """
        old_tags = [tag.name for tag in model.tags]
        tags_to_add = set(tags) - set(old_tags)
        for tag_left in tags_to_add:
            for tag_right in old_tags:
                if tag_left.lower() == tag_right.lower():
                    tags_to_add.remove(tag_left)
        tags_to_del = set(old_tags) - set(tags)
        for tag in tags_to_add:
            t = Tag.query.filter_by(name='%s' % strip_tag(tag)).first()
            if not t:
                t = Tag(strip_tag(tag))
                db.session.add(t)
            else:
                t.times = t.times + 1
                db.session.add(t)
            model.tags.append(t)
        for tag in tags_to_del:
            t = Tag.query.filter_by(name='%s' % strip_tag(tag)).first()
            if t:
                model.tags.remove(t)
                t.times = t.times - 1
                db.session.add(t)
        db.session.add(model)

    @property
    def is_user_followed(self):
        return getUserObject() in self.followers

class User(db.Model):
    """
    用户表
    修改email地址时需要经过验证
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(45), unique=True, nullable=False) # 登陆使用的
    nickname = db.Column(db.String(45), unique=True, nullable=False) # 显示时用的
    password = db.Column(db.String(45), nullable=True)
    is_email_verified = db.Column(db.Boolean, nullable=False)
    slug = db.Column(db.String(45), nullable=True)
    paste_num = db.Column(db.Integer, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    modified_time = db.Column(db.DateTime, nullable=False)
    last_login_time = db.Column(db.DateTime, default=datetime.now())
    privilege = db.Column(db.Integer, default=3)

    info = db.relationship('UserInfo', uselist=False)
    favorites = db.relationship('Paste', secondary=favorite_paste_user,
                        order_by='Paste.created_time', backref="users")
    followers = db.relationship("User", secondary=follow_user_user,
                        primaryjoin=id==follow_user_user.c.from_user_id,
                        secondaryjoin=id==follow_user_user.c.to_user_id)
    followed = db.relationship("User", secondary=follow_user_user,
                        secondaryjoin=id==follow_user_user.c.from_user_id,
                        primaryjoin=id==follow_user_user.c.to_user_id)

    def __init__(self, nickname, email):
        self.nickname = nickname
        self.email = email
        self.paste_num = 0
        self.created_time = self.modified_time = datetime.now()
        self.is_email_verified = True

    def __repr__(self):
        return "<User (%s|%s)>" % (self.nickname, self.email)

    def set_password(self, password):
        self.password = hash_password(password)

    @property
    def url(self):
        if self.slug:
            return url_for('userview.view', slug=self.slug)
        return url_for('userview.view', user_id=self.id)

    @property
    def is_user_followed(self):
        return getUserObject() in self.followers

    @property
    def unread_messages(self):
        return Message.query.filter_by(to_user_id=self.id).all()

    @property
    def followed_users(self):
        return self.followed

    def check_privilege(self, privilege):
        return self.privilege >= privilege

    def get_avatar_url(self, size=128):
        if self.info.avatar:
            return self.info.avatar
        else:
            return "http://www.gravatar.com/avatar/%s?size=%s&d=%s/static/images/avatar/default.jpg" % (
                    hashlib.md5(self.email).hexdigest(),
                    size,
                    request.url_root)

class UserInfo(db.Model):
    """
    用户信息表
    """
    __tablename__ = 'user_info'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    motoo = db.Column(db.String(255))
    introduction = db.Column(db.Text)
    use_gravatar = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(255))

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return "<UserInfo (%s)>" % self.user_id

class Paste(db.Model):
    """
    代码表
    """
    __tablename__ = 'pastes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    syntax_id = db.Column(db.Integer, db.ForeignKey('syntax.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False) # 标题, 默认为"未知标题"
    content = db.Column(db.Text, nullable=False) # 代码内容, 不能为空
    view_num = db.Column(db.Integer, default=0)
    comment_num = db.Column(db.Integer, default=0)
    rate_num = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    created_time = db.Column(db.DateTime, nullable=False)
    modified_time = db.Column(db.DateTime, nullable=False)
    revision = db.Column(db.Integer, nullable=False)
    is_final = db.Column(db.Boolean, default=True, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    is_delete = db.Column(db.Boolean, default=False)

    user = db.relationship(User, backref=db.backref('pastes'))
    syntax = db.relationship(Syntax, backref=db.backref('pastes'))
    followers = db.relationship(User, secondary=follow_user_paste)
    tags = db.relationship('Tag', secondary=paste_tag,
                            order_by=Tag.name, backref="pastes")
    comments = db.relationship('PasteComment', order_by="PasteComment.created_time",
                            backref='pastes')

    def __init__(self, syntax_id, user_id):
        self.syntax_id = syntax_id
        self.title = u'未知标题'
        self.user_id = user_id
        self.view_num = 0
        self.created_time = self.modified_time = datetime.now()
        self.revision = 0
        self.is_private = False

    def __repr__(self):
        return "<Paste (%s@%s)>" % (self.title, self.user_id)

    @property
    def is_user_favorited(self):
        """检查用户是否收藏了该代码"""
        if not getUserObject():
            return None
        return self in getUserObject().favorites

    def get_related_pastes(self, num):
        return Paste.query.filter_by(syntax_id=self.syntax_id).filter(Paste.id!=self.id).filter(Paste.is_private==False).order_by('created_time DESC').all()[:num]

    @property
    def is_user_followed(self):
        return getUserObject() in self.followers

    def get_sliced_title(self, slice):
        if len(self.title) <= slice:
            return self.title
        return "%s ..." % self.title[:slice]

class PasteComment(db.Model):
    """
    评论表
    """
    __tablename__ = 'paste_comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    paste_id = db.Column(db.Integer, db.ForeignKey('pastes.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    modified_time = db.Column(db.DateTime, nullable=False)

    user = db.relationship(User, backref=db.backref('paste_comments'))

    def __init__(self, user_id, paste_id, content):
        self.user_id = user_id
        self.paste_id = paste_id
        self.content = content
        self.created_time = self.modified_time = datetime.now()

    def __repr__(self):
        return "<PasteComment %s>" % self.id

class PasteRate(db.Model):
    """
    paste的打分
    """
    __tablename__ = 'paste_rates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    paste_id = db.Column(db.Integer, db.ForeignKey('pastes.id'))
    rate = db.Column(db.Integer, default=3)
    created_time = db.Column(db.DateTime)

    def __init__(self, user_id, paste_id, rate):
        self.paste_id = paste_id
        self.user_id = user_id
        self.rate = rate

    def __repr__(self):
        return "<PasteRate %s>" % self.id

class Message(db.Model):
    """
    系统消息
    """
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, from_user_id, to_user_id, title, content):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.title = title
        self.content = content

    def __repr__(self):
        return "<Message %s>" % self.id

class MessageTemplate(db.Model):
    """
    系统消息
    """
    __tablename__ = 'message_templates'

    id = db.Column(db.Integer, primary_key=True)
    used_for = db.Column(db.String(45))
    title = db.Column(db.Text)
    content = db.Column(db.Text)

    def __init__(self, used_for, title, content):
        self.used_for = used_for
        self.title = title
        self.content = content

    def __repr__(self):
        return "<MessageTemplate %s|%s>" % (self.id, self.used_for)


class Page(db.Model):
    """
    静态页面
    content使用markdown格式的文本
    """
    __tablename__ = 'pages'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255))
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.now())
    modified_time = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, slug, title, content):
        self.slug = slug
        self.title = title
        self.content = content

    def __repr__(self):
        return "<Page %s|%s>" % (self.id, self.slug)


class Post(db.Model):
    """
    """
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.now())
    modified_time = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def __repr__(self):
        return "<Post %s>" % self.id
