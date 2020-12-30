#!/usr/bin/env python
# -*- coding:utf-8 -*-

# tcp server config
# TCP_CONNECTION_TIMEOUT = 60
TCP_CONNECTION_TIMEOUT = 300

# redis config
REDIS_LIST_KEY = 'redis_list_key_balloon'
EMAIL_REDIS_LIST_KEY = 'email_redis_list_key_balloon'
REDIS_DB_NUM = 0
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_USER = None
REDIS_PASSWORD = None

# remote mysql5.7 config inner address
DB_HOST = '127.0.0.1'
DB_HOST_PORT = 3306
DATA_DB_USER = 'root'
DATA_DB_PASSWORD = 'root'
DATA_DB_NAME = 'table'

# remote upyun image storage config
UPYUN_BUCKET = 'upyun_bucket'
UPYUN_USERNAME = 'upyun_operator'
UPYUN_PASSWORD = 'upyun_password'

# email alert config
EMAIL_SENDER = 'email_sender@example.com'
EMAIL_SENDER_PASSWORD = 'yourpassword'
EMAIL_RECEIVERS = ['email_receiver_1@example.com', 'email_receiver_2@example.com']
IS_NEED_EMAIL_ALERT = False