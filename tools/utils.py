#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    @brief Some assistant method
    @copyright bhyn
    @author km_xu<Annlix@outlook.com>

    PAY ATTENTION:
    This project/application is not open source.
"""

from mysql.connector import connect
from commons.macro import *
from enum import Enum


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
        print(row)
        new_device_id = row['des'] if row is not None else 0
        return new_device_id

    @classmethod
    def get_new_device_config(cls, device: int)->int:
        u = utils()
        sql = f"SELECT * FROM `{DATA_DB_NAME}`.`device_config` WHERE `device_id` = {device} ORDER BY `updated_at` DESC LIMIT 1"
        print(sql)
        u.db_cursor.execute(sql)
        row = u.db_cursor.fetchone()
        return row['id'] if row is not None else 0


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

