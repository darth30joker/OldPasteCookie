#-*-coding:utf-8-*-
import hashlib
import pika
import re
import simplejson as json

from flask import g
from flask import make_response

RABBITMQ_QUEUE = "pastecookie"

def hash_password(password):
    return hashlib.md5(password).hexdigest()

def json_response(data):
    resp = make_response(json.dumps(data), 200)
    resp.headers['Content-Type'] = 'application/json; charset=utf-8'
    return resp

def get_usernames_from_comment(content):
    from pastecookie.models import User
    usernames = [one[1:] for one in re.findall('@\w+', content)]
    users = User.query.filter("nickname IN ('%s')" % ','.join(usernames)).all()
    for user in users:
        content = content.replace('@%s' % user.nickname, '[@%s](%s)' % (user.nickname, user.url))
    return content, users

def send_mail_to_queue(from_user=None, to_user=None, title=None, content=None):
    if not from_user or not to_user or not title or not content:
        return None

    body = json.dumps({'from_user':from_user, 'to_user':to_user, 'title':title, 'content':content})

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=RABBITMQ_QUEUE,
                          properties=pika.BasicProperties(
                            delivery_mode = 2, # make message persistent
                          ),
                          body=body)
    connection.close()

    return True
