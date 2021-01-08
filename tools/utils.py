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
        u.db_cursor.execute(sql)
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_data_index` WHERE `start_at` <= '{ts}' AND `end_at` >= '{ts}' LIMIT 1"
        u.db_cursor.execute(sql)
        row = u.db_cursor.fetchone()
        return row


def get_new_device_id_by_old_device(old_device_id: int) -> int:
    if isinstance(old_device_id, int):
        old_device_id = int(old_device_id)
    with database_resource(is_dict=True) as cursor:
        sql = f"SELECT `des` FROM `{DATA_DB_NAME}`.`mg_relation` WHERE `src` = {old_device_id} AND type = {type}"
        cursor.execute(sql)
        row = cursor.fetchone()
        if (len(row) or row is not None) and row['des'] is not None:
            return row['des']


def get_new_device_config_id_by_old_device_config(old_device_config_id: int) -> int:
    pass


def get_new_id_by_old(old_id: int, data_type: enumerate):
    if isinstance(old_id, int):
        old_id = int(old_id)
    with database_resource(is_dict=True) as cursor:
        sql = f"SELECT `des` FROM `{DATA_DB_NAME}`.`mg_relation` WHERE `src` = {old_id} AND `type` = {data_type}"
        cursor.execute(sql)
        row = cursor.fetchone()
        if (len(row) or row is not None) and row['des'] is not None:
            return row['des']

