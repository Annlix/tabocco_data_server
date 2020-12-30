#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import redis
import logging
import json

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
        print(e)

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
        # print(e)
        return False


def set_redis(data, key):
    try:
        if data:
            redis_connection = connect_redis()
            print(redis)
            redis_connection.set(key, json.dumps(data))
            print(f"Save to {key}@Redis({REDIS_HOST}) SUCCESS")
            return True
        else:
            print(f"Save to {key}@Redis({REDIS_HOST}) Fail")
            return False
    except Exception as e:
        print(e)
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
    # data_to_save = get_data_to_save(request, ts, data)
    # print(data_to_save)
    set_redis("ttt", 'test')
