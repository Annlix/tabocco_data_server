#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    @brief Some assiant method
    @copyright bhyn
    @author km_xu<Annlix@outlook.com>

    PAY ATTENTION:
    This project/application is not opensource.
"""

from db_tools import database_resource
from enum import Enum


class DataType(Enum):
    device = 'device'
    device_configure = 'device_configure'
    device_data = 'device_data'
    user = 'user'
    device_user = 'device_user'


def get_new_device_id_by_old_device(old_device_id: int) -> int:
    if isinstance(old_device_id, int):
        old_device_id = int(old_device_id)
    with database_resource(is_dict=True) as cursor:
        sql = f"SELECT `des` FROM `thcpn`.`mg_relation` WHERE `src` = {old_device_id} AND type = {type}"
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
        sql = f"SELECT `des` FROM `thcpn`.`mg_relation` WHERE `src` = {old_id} AND `type` = {data_type}"
        cursor.execute(sql)
        row = cursor.fetchone()
        if (len(row) or row is not None) and row['des'] is not None:
            return row['des']
