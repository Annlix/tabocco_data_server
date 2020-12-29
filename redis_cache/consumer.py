#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import redis
import argparse
import asyncio

if os.path.split(os.getcwd())[-1] == "redis_cache":
    sys.path.append("..")
from commons.macro import *
from tools.db_tools import *

redis_config = None
redis_connector = None


class RedisConsumer(object):
    """docstring for RedisConsumer"""

    def __init__(self, db=None, key=None, host=REDIS_HOST, port=REDIS_PORT):
        super(RedisConsumer, self).__init__()
        # self.redis_connection = redis.StrictRedis(host=host, port=port, db=db if db else REDIS_DB_NUM)
        self.redis_connection = redis.StrictRedis(host=host, port=port)
        self.key = key if key else REDIS_LIST_KEY
        logging.info(self.key)
        print(self.key)

    def start(self):
        while True:
            try:
                item = self.redis_connection.blpop(self.key)
                logging.info('redis consumer receive alert!')
                print('redis consumer receive alert!')
                json_data = item[1]
                save_json_data(json_data)
            except Exception as e:
                logging.info(e)
                print(e)
                pass


def consumer(loop):
    global redis_connector, redis_config
    if redis_connector is None:
        redis_connector = redis.Redis(host=redis_config['host'],
                                      port=redis_config['port'],
                                      username=redis_config['username'],
                                      password=redis_config['password'],
                                      db=redis_config['db'])
    res = redis_connector.get('foo')
    data = redis_connector.blpop(redis_config['key'])
    print(data)
    if data is not None:
        data = data[1]
        save_json_data(data)
    loop.call_later(1, consumer, loop)


async def task(args, loop):
    try:
        global redis_config
        redis_config = vars(args)
        consumer(loop)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='redis_consumer')
    parser.add_argument('--host',
                        type=str,
                        help='address list key',
                        default=REDIS_HOST)
    parser.add_argument('--port', '-p',
                        type=int,
                        help='port to connect',
                        default=REDIS_PORT)
    parser.add_argument('--db',
                        type=int,
                        help='redis db num',
                        default=REDIS_DB_NUM)
    parser.add_argument('--key',
                        type=str,
                        help='read list key',
                        default=REDIS_LIST_KEY)
    parser.add_argument('--username', '-u',
                        type=str,
                        help="The username of redis auth",
                        default=None)
    parser.add_argument('--password',
                        type=str,
                        help='The password of redis auth',
                        default=REDIS_AUTH)
    args = parser.parse_args()
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(task(args, loop))
        loop.run_forever()
    except Exception as e:
        print(e)
