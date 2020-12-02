#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import sys
import redis
import logging
import functools
sys.path.append('../')
from commons.macro import *
from tools.server_tools import *
from tools.common_tools import *

def insert_into_redis(message, key):
	if IS_NEED_EMAIL_ALERT:
		message = str(message)
		ts = get_datetime_str_from_ts(get_current_ts())
		message = ts + message
		try:
			if message:
				redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
				redis_connection.lpush(key, message)
				return True
			else:
				return False
		except Exception as e:
			logging.info(e)
			print(e)
			return False

def email_wrapper(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		try:
			result = func(*args, **kwargs)
			return result
		except Exception as e:
			logging.info(e)
			print(e)
			result = insert_into_redis(e, EMAIL_REDIS_LIST_KEY)
			return result
	return wrapper

# @email_wrapper
# def _test():
# 	print('twestaetawetawtfgawetawet')
# 	# return 'test'
# 	raise Exception('asdfgasdfgasdfasdfasdfasdf')
#
# if __name__ == '__main__':
# 	a = _test()
# 	print(a)
