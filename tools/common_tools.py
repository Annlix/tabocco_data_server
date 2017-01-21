#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import sys
import time
import logging
import datetime

is_python_3_5 = (sys.version[0:3] == '3.5')

def get_current_ts():
	return int(time.time())

def get_datetime_str_from_ts(ts):
	try:
		global is_python_3_5
		if not is_python_3_5:
			if isinstance(ts, unicode):
				ts = str(ts)
		if isinstance(ts, float):
			ts = str(ts)
			ts = int(ts.split('.')[0])
		elif isinstance(ts, str):
			ts = int(ts.split('.')[0])
			# ts = int(ts)
		dt = datetime.datetime.fromtimestamp(ts)
		dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
		return dt_str
	except Exception as e:
		logging.info(e)
		# print(e)
		return ''

def string2json(string):
	pass

if __name__ == '__main__':
	ts = get_current_ts()
	print(ts)
	print(get_datetime_str_from_ts(ts))
	print(get_datetime_str_from_ts(str(ts)))
