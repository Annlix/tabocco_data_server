#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    @brief Some assistant method
    @copyright bhyn
    @author km_xu<Annlix@outlook.com>

    PAY ATTENTION:
    This project/application is not open source.
"""

import re
import time
import sys
from mysql.connector import connect
from commons.macro import *
from enum import Enum
from datetime import datetime


class DataType(Enum):
    device = 'device'
    device_configure = 'device_configure'
    device_data = 'device_data'
    user = 'user'
    device_user = 'device_user'

class utils():
    
    def __init__(self):
        self.db_connector = connect(host=DB_HOST, port=DB_HOST_PORT, user=DATA_DB_USER, password=DATA_DB_PASSWORD, database=DATA_DB_NAME)
        self.db_cursor = self.db_connector.cursor(dictionary=True)

    @classmethod
    def get_new_device_by_old_device(cls, old_device: int) -> int:
        u = utils()
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`mg_relation` WHERE `src` = {old_device} AND `type` = 'device'"
        u.db_cursor.execute(sql)
        row = u.db_cursor.fetchone()
        new_device_id = row['des'] if row is not None else 0
        return new_device_id

    @classmethod
    def get_new_device_config(cls, device: int)->int:
        u = utils()
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_config` WHERE `device_id` = {device} ORDER BY `updated_at` DESC LIMIT 1"
        u.db_cursor.execute(sql)
        row = u.db_cursor.fetchone()
        return row['id'] if row is not None else 0
    
    @classmethod
    def get_data_table_name(cls, data):
        u = cls()
        ts = data['ts']
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_data_index` WHERE `start_at` <= '{ts}' AND `end_at` >= '{ts}' LIMIT 1"
        u.db_cursor.execute(sql)
        row = u.db_cursor.fetchone()
        if row is not None:
            return row['tb_name']
        else:
            return cls.create_data_table(ts)
    
    @classmethod
    def get_last_day(cls, ts):
        if isinstance(ts, datetime):
            if ts.month == 2:
                if cls.is_leap_year(ts):
                    return 29
                else:
                    return 28
            elif ts.month in (1, 3, 5, 7, 8, 10, 12):
                return 31
            else:
                return 30

    @classmethod
    def is_leap_year(cls, ts):
        year = ts.year
        if year % 100 == 0:
            return year % 400 == 0
        else:
            return year % 4 == 0
    
    @classmethod
    def create_data_table(cls, ts):
        u = cls()
        if isinstance(ts, str):
            if re.match(r"^[0-9]+$", ts):
                ts = int(ts)
                ts = datetime.fromtimestamp(ts)
            else:
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        start_date = datetime.strptime(ts.strftime("%Y-%m-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(ts.strftime(f"%Y-%m-{cls.get_last_day(ts)} 23:59:59"), "%Y-%m-%d %H:%M:%S")
        sql = f"INSERT INTO `{DATA_DB_NAME}`.`device_data_index` (`start_at`, `end_at`, `tb_name`) VALUE('{start_date}', '{end_date}', 'device_data_')"
        u.db_cursor.execute(sql)
        tb_id = u.db_cursor.lastrowid
        sql = f"UPDATE `{DATA_DB_NAME}`.`device_data_index` SET `tb_name` = 'device_data_{tb_id}' WHERE `id` = {tb_id}"
        u.db_cursor.execute(sql)
        sql = """
        CREATE TABLE IF NOT EXISTS `device_data_{table_id}` (
          `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
          `device_config_id` int(10) unsigned NOT NULL,
          `device_id` int(10) unsigned NOT NULL,
          `data` json NOT NULL,
          `ts` timestamp NULL DEFAULT NULL,
          `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `deleted_at` timestamp NULL DEFAULT NULL,
          `type` enum('image','data') COLLATE utf8mb4_unicode_ci NOT NULL,
          `uuid` char(36) CHARACTER SET utf8 NOT NULL,
          PRIMARY KEY (`id`),
          KEY `device_id_ts_{table_id}` (`device_id`,`ts`),
          KEY `device_data_device_config_id_{table_id}` (`device_config_id`,`device_id`) USING BTREE
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        sql = sql.format(table_id=tb_id)
        print(u.db_cursor.execute(sql))
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_data_index` WHERE `start_at` <= '{ts}' AND `end_at` >= '{ts}' LIMIT 1"
        u.db_cursor.execute(sql)
        row = u.db_cursor.fetchone()
        print(row)
        return row

    @classmethod
    def check_config_version(cls, config):
        if isinstance(config, list):
            for item in config:
                return 'v2' if 'params' in item else 'v1'
        return None
    
    @classmethod
    def check_device_exists(cls, device:int):
        u = cls()
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`devices` WHERE `id` = {device} LIMIT 1"
        u.db_cursor.execute(sql)
        res = u.db_cursor.fetchone()
        if res is None or not res['version'] == '2.0':
            sql = f"SELECT * FROM `{DATA_DB_NAME}`.`mg_relation` WHERE `src` = {device} LIMIT 1"
            u.db_cursor.execute(sql)
            res = u.db_cursor.fetchone()
            if res is None:
                return False
            else:
                sql = f"SELECT * FROM `{DATA_DB_NAME}`.`devices` WHERE `id` = {res['des']} LIMIT 1"
                u.db_cursor.execute(sql)
                res = u.db_cursor.fetchone()
                if res is None:
                    return False
                else:
                    return res
        else:
            # Check the device version
            if res['version'] == '2.0':
                if isinstance(res, int):
                    sql = f"SELECT * FROM `devices` WHERE `id` = {res}"
                    u.db_cursor.execute(sql)
                    res = u.db_cursor.fetchone()
                else:
                    return res

    @classmethod
    def check_device_config_exists(cls, device_config_id: int, device: dict):
        u = cls()
        if isinstance(device, int):
            sql = f"SELECT * FROM `{DATA_DB_NAME}`.`devices` WHERE `id` = {device} LIMIT 1"
            u.db_cursor.execute(sql)
            device = u.db_cursor.fetchone()
        if device['version'] == '2.0':
            sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_config` WHERE `id` = {device_config_id} LIMIT 1"
            u.db_cursor.execute(sql)
            res = u.db_cursor.fetchone()
            if res is None:
                return False
            else:
                if res['device_id'] == device['id']:
                    return res
                else:
                    return False
        else:
            sql = f"SELECT * FROM `{DATA_DB_NAME}`.`mg_relation` WHERE `src` = {device_config_id} LIMIT 1"
            u.db_cursor.execute(sql)
            res = u.db_cursor.fetchone()
            if res is None:
                return False
            else:
                new_config_id = res['des']
                sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_config` WHERE `id` = {new_config_id} LIMIT 1"
                u.db_cursor.execute(sql)
                res = u.db_cursor.fetchone()
                if res is None:
                    return False
                else:
                    if res['device_id'] == device['id']:
                        return res
                    else:
                        return False

    @classmethod
    def get_real_device(cls, device):
        if isinstance(device, int):
            device_id = device
            t = 'int'
        elif isinstance(device, dict):
            device_id = device['id']
            t = 'dict'
        device_info = cls.check_device_exists(device_id)
        if not device_info == False:
            return device_info['id'] if t == 'int' else device_info
        else:
            return None
    
    @classmethod
    def get_real_config(cls, device_config, device):
        if isinstance(device_config, int):
            device_config_id = device_config
            t = 'int'
        elif isinstance(device_config, dict):
            device_config_id = device_config['id']
            t = 'dict'
        if isinstance(device, int):
            device_id = device
        elif isinstance(device, dict):
            device_id = device['id']
        device_config_info = cls.check_device_config_exists(device_config_id, device_id)
        if not device_config_info == False:
            return device_config_info['id'] if t == 'int' else device_config_info
        else:
            return None
