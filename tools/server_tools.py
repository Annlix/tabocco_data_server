#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import redis
import json
import logging

sys.path.append('../')
from commons import macro
from tools.common_tools import *
from tools.db_tools import *
from redis_cache import email_producer
import demjson


def get_reply_json(request=None, is_failed=False):
    try:
        # print('line 1')
        reply = {}
        if is_failed:
            reply = {'method': 'failed', 'ts': get_current_ts()}
        else:
            method = request['method']
            reply = {'method': '', 'ts': get_current_ts()}
            if method == 'push_data':
                reply['method'] = 'data_uploaded'
                reply['device_id'] = request['device_id']
            if method == 'push_image':
                reply['method'] = 'push_image_ready'
                reply['device_id'] = request['device_id']
            if method == 'pushing_image':
                reply['method'] = 'image_uploaded'
            if method == 'push_data_size':
                reply['method'] = 'push_data_ready'
                reply['device_id'] = request['device_id']
            if method == 'update_device_info':
                reply['method'] = 'update_device_info'
                reply['device_id'] = request['device_id']
            if method == 'update_time':
                reply = {'ts': get_current_ts()}
        # reply_str = json.dumps(reply) + b'\x03'
        reply_str = demjson.encode(reply, encoding="utf8")
        email_producer.insert_into_redis(reply_str, macro.EMAIL_REDIS_LIST_KEY)
        return reply_str
    except Exception as e:
        logging.info(e)
        print(e)
        return demjson.encode({'method': 'failed', 'ts': get_current_ts()})
    # return json.dumps({'method':'failed','ts':get_current_ts()}) + b'\x03'


def get_reply_string(request=None, is_failed=False):
    try:
        reply = ''
        if is_failed:
            reply = 'method:failed,ts:' + str(get_current_ts())
        else:
            method = request['method']
            if method == 'push_data':
                reply = 'method:push_data_ready,ts:' + str(get_current_ts())
            if method == 'push_data_finish':
                reply = 'method:data_uploaded,ts:' + str(get_current_ts())
            if method == 'push_image':
                reply = 'method:push_image_ready,ts:' + str(get_current_ts())
            if method == 'pushing_image':
                reply = 'method:image_uploaded,ts:' + str(get_current_ts())
        return reply.encode('utf-8') + b'\x03'
    except Exception as e:
        logging.info(e)
        print(e)
        return 'method:failed,ts:' + str(get_current_ts()) + b'\x03'


def get_data_to_save(request, ts, data):
    try:
        tmp_data = {'type': 'data', 'device_id': request['device_id'], 'device_config_id': request['device_config_id'],
                    'data': data, 'ts': get_datetime_str_from_ts(ts)}
        # add type of data
        return tmp_data
    except Exception as e:
        logging.info(e)
        email_producer.insert_into_redis(e, macro.EMAIL_REDIS_LIST_KEY)
        return None


def get_image_info_to_save(request):
    try:
        if request:
            tmp_data = {}
            tmp_data['type'] = 'image'
            tmp_data['device_id'] = request['device_id']
            tmp_data['device_config_id'] = request['device_config_id']
            tmp_data['data'] = request['image_info']
            # add the type of data
            tmp_data['type'] = 'image'
            tmp_data['ts'] = get_datetime_str_from_ts(request['ts'])
            # tmp_data['ts'] = get_datetime_str_from_ts(request['acquisition_time'])
            return tmp_data
        else:
            return None
    except Exception as e:
        logging.info(e)
        email_producer.insert_into_redis(e, macro.EMAIL_REDIS_LIST_KEY)
        return None


def convert_request_to_dict(request):
    try:
        request = request.replace('\r', '')
        request = request.replace('\n', '')
        request_list = request.split(',')
        request_dict = {}
        for i in xrange(0, len(request_list)):
            tmp_list = (request_list[i]).split(':')
            key = tmp_list[0]
            value = tmp_list[1]
            request_dict[key] = value
        return request_dict
    except Exception as e:
        logging.info(e)
        return None


if __name__ == '__main__':
    # get_reply_json
    print(get_reply_json(is_failed=True))
    print(get_reply_json({"method": "push_data", "device_id": 1}))
    print(get_reply_json({"method": "push_image", "device_id": 1}))
    print(get_reply_json({"method": "pushing_image", "device_id": 1}))
    # get_data_to_save
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
    data_to_save = get_data_to_save(request, ts, data)
    redis_connection = redis.StrictRedis()
    redis_connection.lpush('redis_list_key_1', json.dumps(data_to_save))
    item = redis_connection.blpop('redis_list_key_1')
    json_data = item[1]
    save_json_data(json_data)
    # get_image_info_to_save
    request = {
        'device_id': 1,
        'device_config_id': 1,
        'image_info': {
            'user_defined_key': {
                'url': '/root/home/project/images/1/1.jpg'
            }
        },
        'acquisition_time': 1484391381
    }
    image_info_to_save = get_image_info_to_save(request)
    redis_connection = redis.StrictRedis()
    redis_connection.lpush('redis_list_key_1', json.dumps(image_info_to_save))
    item = redis_connection.blpop('redis_list_key_1')
    json_data = item[1]
    save_json_data(json_data)
