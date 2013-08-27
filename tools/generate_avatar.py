#!/usr/bin/env python
#-*-coding:utf-8-*-
"""
这个代码的主要作用, 是从gravatar下拿到用户的头像图片, 然后存到服务器上
会使用crontab来定期执行, 定期更新用户的头像

做的操作有:
1. 连接数据库
2. 得到所有use_gravatar为True的用户列表
3. 去gravatar下下载头像
4. 如果失败, 则什么也不做
5. 如果成功, 则保存下来
"""
import os
import hashlib
import urllib
import shutil
import psycopg2
import psycopg2.extras

def sumfile(filename):
    '''Returns an md5 hash for an object with read() method.'''
    f = open(filename, "rb")
    m = hashlib.new("md5")
    while True:
        d = f.read(8096)
        if not d:
            break
        m.update(d)
    f.close()
    return m.hexdigest()

def download_and_replace(url, filename, tempfile):
    try:
        urllib.urlretrieve(url, tempfile)
    except:
        return False
    if not os.path.exists(filename):
        shutil.move(tempfile, filename)
        return True
    else:
        if sumfile(filename) != sumfile(tempfile):
            shutil.move(tempfile, filename)
            return True
    return False

DBNAME = "daimaduan"
DBUSER = "daimaduan"
DBPASS = "daimaduan"

conn = psycopg2.connect(database=DBNAME, user=DBUSER, password=DBPASS, host="localhost")
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cursor.execute("SELECT users.id AS user_id, users.email AS user_email, "
               "user_info.avatar AS user_avatar, user_info.use_gravatar AS use_gravatar "
               "FROM users LEFT JOIN user_info ON user_info.user_id = users.id "
               "WHERE user_info.use_gravatar is True")

users = cursor.fetchall()

default_avatar = "http://daimaduan.com/static/images/avatar/default.jpg"
for user in users:
    try:
        download_and_replace("http://gravatar.com/avatar/%s?size=150&d=%s" % (hashlib.md5(user['user_email']).hexdigest(), default_avatar),
                             "daimaduan/static/images/avatar/%s.jpg" % user['user_id'],
                             "/tmp/daimaduan_temp.png")
        filename = "http://daimaduan.com/static/images/avatar/%s.jpg" % user['user_id']
    except Exception, e:
        filename = default_avatar

    if user['user_avatar'] == "" or user['user_avatar'] is None:
        sql = "UPDATE user_info SET avatar = '%s' WHERE user_id = %s" % (filename, user['user_id'])
        cursor.execute(sql)

conn.commit()
