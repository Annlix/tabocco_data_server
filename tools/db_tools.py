#!/usr/bin/env python
# coding=utf-8

import sys
import json
import random
import logging
import mysql.connector
import json
from pip._internal.utils import temp_dir
import traceback

sys.path.append('../')
from commons.macro import *
from tools.common_tools import get_current_ts
from tools.upyun_tools import save_to_upyun
from models import Database_session, Device_config, Device_data, Database_session_sunsheen, \
    device_config, Device, Device_data_confirm
from importlib import reload
from tools.utils import *
from tools.aliyun_tools import *

reload(sys)


# sys.setdefaultencoding('utf-8')

def create_engine(user, password, database, host='127.0.0.1', port=3306, **kw):
    params = dict(user=user, password=password, database=database, host=host, port=port)
    defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
    for k, v in defaults.items():
        params[k] = kw.pop(k, v)
    params.update(kw)
    params['buffered'] = True
    engine = mysql.connector.connect(**params)
    return engine


class database_resource:
    def __init__(self, user=DATA_DB_USER, password=DATA_DB_PASSWORD, database=DATA_DB_NAME, host=DB_HOST,
                 port=DB_HOST_PORT, is_dict=False):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.is_dict = is_dict

    def __enter__(self):
        self.conn = create_engine(self.user, self.password, self.database, self.host, self.port)
        self.cursor = self.conn.cursor(dictionary=self.is_dict)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()


def get_latest_device_config_json(device_id):
    try:
        if not isinstance(device_id, int):
            device_id = int(device_id)
        param = {}
        logging.info(device_id)
        with database_resource(is_dict=True) as cursor:
            # Check if the device is exists
            sql = f"SELECT * FROM `device_config` WHERE `device_id` = {device_id}"
            logging.info(sql)
            cursor.execute(sql)
            value = cursor.fetchone()
            data = json.loads(value['data'])
            control = json.loads(value['control'])
            param['device_id'] = device_id
            param['device_config_id'] = value['id']
            param['data'] = data
            param['image'] = json.loads(value['image'])
            # if utils.check_config_version(data) == 'v1':
            #     param['data'] = convert_data_config_new(data)
            #     param['image'] = convert_image_config_new(data)
            # else:
            #     param['data'] = convert_data_config(data)
            #     param['image'] = convert_image_config(data)
            param['control'] = control
            param['ts'] = get_current_ts()
        return json.dumps(param)
    except Exception as e:
        traceback.print_exc()
        logging.info(e)
        return None


def get_latest_device_config_string(device_id):
    try:
        if not isinstance(device_id, int):
            device_id = int(device_id)
        param = ''
        with database_resource() as cursor:
            sql = 'select `%s`, `%s`, `%s` from `%s` where `%s` = %d order by id desc' % (
            'id', 'data', 'control', 'device_config', 'device_id', device_id)
            cursor.execute(sql)
            value = cursor.fetchone()
            device_config_id = value[0]
            data = json.loads(value[1])
            control = json.loads(value[2])
            param = '[common]'
            param = param + 'device_id=' + str(device_id) + ';';
            param = param + 'device_config_id=' + str(device_config_id) + ';';
            param = param + 'ts=' + str(get_current_ts()) + ';';
            param = param + '[control]';
            for k, v in control.items():
                param = param + k + '=' + v + ';'
            for k, v in data.items():
                param = param + '[' + str(k) + ']'
                for key, value in v.items():
                    param = param + str(key) + '=' + str(value) + ';'
        return param + b'\x03'
    except Exception as e:
        logging.info(e)
        traceback.print_exc()
        return None


def convert_data_config(data):
    tmp_list = []
    if isinstance(data, dict):
        tmp_dict = {}
        if data['port'] != 'image':
            port = data['port'] if 'port' in data else ''
            port_num = data['port_num'] if 'port_num' in data else 0
            data_num = str(data['data_num']) if 'data_num' in data else '0'
            desc = data['desc'] if 'desc' in data else ''
            name = data['name'] if 'name' in data else ''
            sensor_type = data['sensor_type'] if 'sensor_type' in data else ''
            tmp_dict_key = name + str(port_num)
            if tmp_dict_key in tmp_dict:  # Fixed compatibility issues between in python2 and python 3
                tmp_dict[tmp_dict_key]['keys'][data_num] = data_num
            else:
                tmp_dict[tmp_dict_key] = {}
                tmp_dict[tmp_dict_key]['port'] = port
                tmp_dict[tmp_dict_key]['port_num'] = port_num
                tmp_dict[tmp_dict_key]['sensor_type'] = sensor_type
                tmp_dict[tmp_dict_key]['keys'] = {}
                tmp_dict[tmp_dict_key]['keys'][data_num] = data_num
            for value in tmp_dict.values():
                tmp_list.append(value)
            return tmp_list
    elif isinstance(data, list):
        for item in data:
            tmp_list = tmp_list + convert_data_config(item)
        return tmp_list


def convert_image_config(data, index=0):
    tmp_list = list()
    if isinstance(data, dict):
        tmp_dict = {}
        if data['port'] == 'image':
            port = data['port'] if 'port' in data else None
            port_num = data['port_num'] if 'port_num' in data else None
            data_num = str(data['data_num']) if 'data_num' in data else None
            desc = data['desc']  if 'desc' in data else None
            name = data['name'] if 'name' in data else 'Unknown Name'
            sensor_type = data['sensor_type'] if 'sensor_type' in data else None
            tmp_dict_key = name + str(port_num)
            if tmp_dict_key in tmp_dict:
                tmp_dict[tmp_dict_key]['keys'][data_num] = index
            else:
                tmp_dict[tmp_dict_key] = {}
                tmp_dict[tmp_dict_key]['port'] = port
                tmp_dict[tmp_dict_key]['port_num'] = port_num
                tmp_dict[tmp_dict_key]['sensor_type'] = sensor_type
                tmp_dict[tmp_dict_key]['keys'] = {}
                tmp_dict[tmp_dict_key]['keys'][data_num] = index
        for value in tmp_dict.values():
            tmp_list.append(value)
        return tmp_list
    else:
        for item in data:
            tmp_list = tmp_list + convert_image_config(item, data.index(item))
        return tmp_list


def convert_data_config_new(data):
    config_list = []
    for v in data:
        if v['port'] != 'Img':
            tmp = {}
            tmp['port'] = v['port'] if 'port' in v else ''
            tmp['port_num'] = v['port_num'] if 'port_num' in v else 0
            tmp['sensor_type'] = v['sensor_type'] if 'sensor_type' in v else ''
            tmp['keys'] = {}
            for param in v['params']['contents']:
                data_num = param['data_num'] if 'data_num' in param else 'unknown_data_num'
                tmp['keys'][str(data_num)] = param['key']
            config_list.append(tmp)
    return config_list


def convert_image_config_new(data):
    config_list = []
    for v in data:
        if v['port'] == 'Img':
            tmp = {}
            tmp['port'] = v['port']
            tmp['port_num'] = v['port_num']
            tmp['sensor_type'] = v['sensor_type']
            tmp['keys'] = {}
            for param in v['params']:
                data_num = param['data_num'] if 'data_num' in param else 'unknown_data_num'
                tmp['keys'][str(data_num)] = param['key']
            config_list.append(tmp)
    return config_list


'''
def get_latest_device_config_json(device_id):
    try:
        if not isinstance(device_id, int):
            device_id = int(device_id)
        param = {}
        with Database_session() as session:
            results = session.query(Device_config).filter_by(device_id = device_id)
            result = results.order_by(Device_config.id.desc()).first()
            param['device_config_id'] = result.id
            param['device_id'] = result.device_id
            param['method'] = 'push_param'
            param['config'] = result.data
            param['control'] = result.control
            param['ts'] = get_current_ts()
        return json.dumps(param)
    except Exception as e:
        logging.info(e)
        # print(e)
        return None
'''


# def save_json_data(json_data):
#     try:
#         dict_data = json.loads(json_data)
#         if not isinstance(dict_data['device_id'], int):
#             dict_data['device_id'] = int(dict_data['device_id'])
#         if not isinstance(dict_data['device_config_id'], int):
#             dict_data['device_config_id'] = int(dict_data['device_config_id'])
#         db_name = ''
#         with database_resource() as cursor:
#             if dict_data['type'] == 'image':
#                 db_name = 'device_data'
#                 # db_name = 'device_image'
#                 if save_to_upyun(dict_data):
#                     sql = "insert into `%s` (`device_id`, `device_config_id`, `ts`, `data`) values \
#                                 (%d, %d, '%s', '%s')"%(db_name, dict_data['device_id'], dict_data['device_config_id'], dict_data['ts'], json.dumps(dict_data['data']))
#                     cursor.execute(sql)
#             else:
#                 db_name = 'device_data'
#                 sql = "insert into `%s` (`device_id`, `device_config_id`, `ts`, `data`) values \
#                             (%d, %d, '%s', '%s')"%(db_name, dict_data['device_id'], dict_data['device_config_id'], dict_data['ts'], json.dumps(dict_data['data']))
#                 cursor.execute(sql)
#             print('after execution')
#             logging.info('after execution')
#     except Exception as e:
#         logging.info(e)
#         print(e)
#         pass


def save_json_data(json_data):
    try:
        dict_data = json.loads(json_data)
        if not isinstance(dict_data['device_id'], int):
            dict_data['device_id'] = int(dict_data['device_id'])
        if not isinstance(dict_data['device_config_id'], int):
            dict_data['device_config_id'] = int(dict_data['device_config_id'])
        old_device_id = dict_data['device_id']
        old_device_config_id = dict_data['device_config_id']
        dict_data['device_id'] = utils.get_real_device(dict_data['device_id'])
        dict_data['device_config_id'] = utils.get_real_config(dict_data['device_id'], dict_data['device_config_id'])
        with Database_session() as session:
            if dict_data['device_id'] is not None and dict_data['device_config_id'] is not None:
                # new_id = utils.get_new_device_by_old_device(dict_data['device_id'])
                # if new_id == 0:
                #     raise Exception("This device can't found in new database.")
                # new_config_id = utils.get_new_device_config(new_id)
                # if new_config_id == 0:
                #     raise Exception("This device configure is not exists.")
                # dict_data['device_id'] = new_id
                # dict_data['device_config_id'] = new_config_id
                if dict_data['type'] == 'image':
                    if save_to_upyun(dict_data):
                        AliyunOss.upload_image(dict_data)
                        Device_data.__table__.name = utils.get_data_table_name(dict_data)
                        device_image_data = Device_data(device_id=dict_data['device_id'],
                                                        device_config_id=dict_data['device_config_id'],
                                                        type=dict_data['type'], ts=dict_data['ts'], data=dict_data['data'])
                        print("SAVED", device_image_data.__dict__)
                        session.add(device_image_data)
                        if dict_data['device_id'] == 54:
                            device_image_data_sunsheen = Device_data(device_id=dict_data['device_id'],
                                                                    device_config_id=dict_data['device_config_id'],
                                                                    ts=dict_data['ts'], data=dict_data['data'])
                            print("SAVED", device_image_data_sunsheen.__dict__)
                            save_json_data_sunsheen(device_image_data_sunsheen)
                    else:
                        print("Save image to upyun fail")
                else:
                    Device_data.__table__.name = utils.get_data_table_name(dict_data)
                    device_value_data = Device_data(device_id=dict_data['device_id'],
                                                    type=dict_data['type'],
                                                    device_config_id=dict_data['device_config_id'],
                                                    ts=dict_data['ts'],
                                                    data=dict_data['data'])
                    print("SAVED", device_value_data.__dict__)
                    session.add(device_value_data)
                    if dict_data['device_id'] == 54:
                        device_value_data_sunsheen = Device_data(device_id=dict_data['device_id'],
                                                                device_config_id=dict_data['device_config_id'],
                                                                ts=dict_data['ts'], data=dict_data['data'])
                        print("SAVED", device_value_data_sunsheen.__dict__)
                        save_json_data_sunsheen(device_value_data_sunsheen)
                logging.info('after execution')
            else:
                device_data_confirm = Device_data_confirm(source_device_id = old_device_id, 
                                                      source_config_id = old_device_config_id, 
                                                      new_device_id = dict_data['device_id'],
                                                      new_config_id = dict_data['device_config_id'],
                                                      data = dict_data['data'],
                                                      ts = dict_data['ts'])
                session.add(device_data_confirm)
                error_msg = dict(dict_data, **dict(old_device_id=old_device_id, old_device_config_id=old_device_config_id))
                logging.error(f"Save data error because the device informaion is not match:{json.dumps(error_msg)}")
    except Exception as e:
        logging.info(e)
        traceback.print_exc()


def save_json_data_sunsheen(data):
    try:
        with Database_session_sunsheen() as session:
            session.add(data)
    except Exception as e:
        logging.info(e)
        traceback.print_exc()
        pass


def _save_device_config(data):
    device_id = data['device_id']
    config = json.dumps(data['config'])
    control = json.dumps(data['control'])
    with database_resource() as cursor:
        sql = "insert into `%s` (`device_id`, `data`, `control`) \
        values (%d, '%s', '%s')" % ('device_config', device_id, config, control)
        cursor.execute(sql)


if __name__ == '__main__':
    # control = {
    #     "img_capture_invl": "*/30 * * * *",
    #     "img_upload_invl": "*/30 * * * *",
    #     "data_capture_invl": "*/30 * * * *",
    #     "data_upload_invl": "*/30 * * * *"
    # }
    # config = {
    #     "t_30": {
    #         "port": "AD1",
    #         "unit": "x",
    #         "type": "temperature",
    #         "desc": "30depth temperature"
    #     },
    #     "t_10": {
    #         "port": "AD2",
    #         "unit": "x",
    #         "type": "temperature",
    #         "desc": "10depth temperature"
    #     }
    # }
    # config = {
    #     't_30': {
    #         'port': 'AD1',
    #         'unit': 'x',
    #         'type': 'temperature',
    #         'desc': '30depth temperature',
    #         'max_v': 100,
    #         'min_v': 0
    #     },
    #     't_10': {
    #         'port': 'AD2',
    #         'unit': 'x',
    #         'type': 'temperature',
    #         'desc': '10depth temperature',
    #         'max_v': 100,
    #         'min_v': 0
    #     }
    # }
    # control = {
    #     'img_capture_invl': '*/30 * * * *',
    #     'img_upload_invl': '*/30 * * * *',
    #     'data_capture_invl': '*/30 * * * *',
    #     'data_upload_invl': '*/30 * * * *'
    # }
    # device_config_data_to_save = {
    #     'device_id': random.randint(0,100),
    #     'config': config,
    #     'control': control
    # }
    # _save_device_config(device_config_data_to_save)
    # device_config_data_query = get_latest_device_config_json(65)
    # print(device_config_data_query)
    # json_data_to_save = json.dumps({
    #     "type": "data",
    #     "device_config_id": 1,
    #     "device_id": 1,
    #     "data": {
    #         "t_30": {
    #             "value": 5
    #         }
    #     },
    #     "ts": "2017-01-07 16:33:54"
    # })
    # json_data_to_save = json.dumps({
    #     'type': 'data',
    #     'device_config_id': 1,
    #     'device_id': 1,
    #     'data': {
    #         't_30': {
    #             'value': 5
    #         }
    #     },
    #     'ts': '2017-01-07 16:33:54'
    # })

    # save_json_data(json_data_to_save)
    # get_latest_device_config_json(5)
    get_latest_device_config_string(5)
    test_config = {
        'key1':
            {
                'port': 'string',
                'port_num': 0,
                'data_num': 0,
                'desc': 'string',
                'name': 'string1',
                'sensor_type': 'sensorNo'
            },
        'key2':
            {
                'port': 'string',
                'port_num': 0,
                'data_num': 1,
                'desc': 'string',
                'name': 'string1',
                'sensor_type': 'sensorNo'
            },
        'key3':
            {
                'port': 'string',
                'port_num': 1,
                'data_num': 0,
                'desc': 'string',
                'name': 'string2',
                'sensor_type': 'sensorNo'
            },
        'key4':
            {
                'port': 'string',
                'port_num': 1,
                'data_num': 1,
                'desc': 'string',
                'name': 'string2',
                'sensor_type': 'sensorNo'
            },
        'key5':
            {
                'port': 'image',
                'port_num': 1,
                'data_num': 1,
                'desc': 'string',
                'name': 'string2',
                'sensor_type': 'sensorNo'
            }
    }
    convert_data_config(test_config)
    convert_image_config(test_config)
