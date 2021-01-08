#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import sys
import json
import redis
import logging
import argparse
import traceback
sys.path.append('../')
from commons.macro import *
# from tools.db_tools import save_json_data
from tools.email_tools import send_alert_email

class RedisConsumer(object):
	"""docstring for RedisConsumer"""
	def __init__(self, db=None, key=None, host='localhost', port=6379):
		super(RedisConsumer, self).__init__()
		# self.redis_connection = redis.StrictRedis(host=host, port=port, db=db if db else REDIS_DB_NUM)
		self.redis_connection = redis.StrictRedis(host=host, port=port)
		self.key = key if key else EMAIL_REDIS_LIST_KEY

	def start(self):
		while True:
			try:
				item=self.redis_connection.blpop(self.key)
				logging.info('email consumer receive data!')
				alert_message = item[1]
				send_alert_email(alert_message)
			except Exception as e:
				logging.info(e)
				traceback.print_exc()
				pass


if __name__ == '__main__':
	# parser = argparse.ArgumentParser(description='redis_consumer')
	# parser.add_argument('--db', type=int, 
	# 	help='redis db num', default=None)
	# parser.add_argument('--key', type=str, 
	# 	help='read list key', default=None)
	# parser.add_argument('--host', type=str, 
	# 	help='address list key', default='localhost')
	# parser.add_argument('--port', type=int, 
	# 	help='port to connect', default=6379)
	# args = parser.parse_args()
	# redis_consumer = RedisConsumer(args.db, args.key, args.host, args.port)
	redis_consumer = RedisConsumer()
	try:
		redis_consumer.start()
	except KeyboardInterrupt:
		pass