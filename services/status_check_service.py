#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
from datetime import *
sys.path.append('../')
from models import Database_session, Station, Device, Device_data


def status_check(threshold):
    with Database_session() as session:
        stations = session.query(Station).all()
        # print(len(stations))
        for station in stations:
            station.status = 'normal'
            if station.deleted_at:
                station.status = 'abnormal'
                continue
            devices = station.devices
            if not devices:
                station.status = 'abnormal'
                continue
            for device in devices:
                if device.deleted_at:
                    device.status = 'abnormal'
                    continue
                device.status = 'normal'
                device_lastest_data = session.query(Device_data).filter_by(device_id = device.id).order_by(Device_data.created_at.desc()).first()
                if device_lastest_data is None:
                    device.status = 'abnormal'
                    station.status = 'abnormal'
                    continue
                tmp = datetime.utcnow() + timedelta(hours = 8) - device_lastest_data.created_at # Beijing timezone 8 hours later than utc zone !
                if tmp > timedelta(hours = threshold):
                    device.status = 'abnormal'
                    station.status = 'abnormal'


# should only be called by server.py
def initialize_service_bash():
    python_execution_path = sys.executable
    service_file_path = os.path.join(sys.path[0], 'services/status_check_service.py')
    service_bash_path = os.path.join(sys.path[0], 'services/status_check.sh')
    bash_header = '#! /bin/bash' + '\n'
    bash_body = python_execution_path + ' ' + service_file_path
    with open(service_bash_path, 'wb+') as f:
    	f.write(bash_header.encode('utf-8'))
    	f.write('\n'.encode('utf-8'))
    	f.write(bash_body.encode('utf-8'))
    return


if __name__ == '__main__':
       status_check(6)
       print('check finish !')
