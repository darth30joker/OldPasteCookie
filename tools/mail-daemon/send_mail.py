#!/usr/bin/env python
#-*-coding:utf-*-
import pika
import simplejson as json
from daemon import Daemon

PID_FILE = "/tmp/daimaduan_send_mail.pid"
STDOUT = "/var/log/daimaduan_send_mail.out"
STDERR = "/var/log/daimaduan_send_mail.err"

RABBITMQ_HOST = "localhost"
RABBITMQ_QUEUE = "daimaduan"

def callback(ch, method, properties, body):
    message = json.loads(body)
    print message
    ch.basic_ack(delivery_tag = method.delivery_tag)

def send_mail():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    channel.queue_declare(queue=RABBITMQ_QUEUE,
                          durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,
                          queue=RABBITMQ_QUEUE)

    channel.start_consuming()

if __name__ == '__main__':
    """
    daemon = Daemon(PID_FILE, stdout=STDOUT, stderr=STDERR, func=send_mail)
    daemon.start()
    """
    send_mail()
