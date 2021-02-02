#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import redis
import logging
import json
import traceback

sys.path.append('../')
from commons.macro import *
from tools.server_tools import *

def connect_redis():
    try:
        redis_connector = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, username=REDIS_USER, password=REDIS_PASSWORD)
        if redis_connector.ping():
            return redis_connector
        else:
            raise Exception("Connect redis fail.")
    except Exception as e:
        traceback.print_exc()

def insert_into_redis(data, key):
    try:
        if data:
            redis_connection = connect_redis()
            logging.info(key)
            logging.info(data)
            redis_connection.lpush(key, json.dumps(data))
            return True
        else:
            return False
    except Exception as e:
        logging.info(e)
        traceback.print_exc()
        return False


def set_redis(data, key):
    try:
        if data:
            redis_connection = connect_redis()
            if not isinstance(data, str):
                data = json.dumps(data)
            redis_connection.set(key, json.dumps(data))
            return True
        else:
            return False
    except Exception as e:
        traceback.print_exc()
        logging.info(e)
        return False


if __name__ == '__main__':
    request = {
        'device_id': 1,
        'device_config_id': 1,
    }
    ts = '1484391385'
    data = {
        't_30': {
            'value': 5
        }
    }
    set_redis("ttt", 'test')
