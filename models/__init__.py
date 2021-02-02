#!/usr/bin/env python
# -*- coding:utf-8 -*-

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
import sys

sys.path.append('../')
from models.base import Base
from models.app import App
from models.device import Device
from models.station import Station
from models.device_config import Device_config
from models.device_data import Device_data
from models.device_data_confirm import Device_data_confirm
from commons.macro import *

# dialect+driver://username:password@host:port/
_engine = create_engine(
    'mysql+mysqlconnector://%s:%s@%s:%d/%s' % (DATA_DB_USER, DATA_DB_PASSWORD, DB_HOST, DB_HOST_PORT, DATA_DB_NAME))

_Session = sessionmaker(bind=_engine)


class Database_session:
    def __enter__(self):
        self.session = _Session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()


_engine_sunsheen = create_engine(
    'mysql+mysqlconnector://%s:%s@%s:%d/%s' % (DATA_DB_USER, DATA_DB_PASSWORD, DB_HOST, DB_HOST_PORT, 'sunsheen'))
_Session_sunsheen = sessionmaker(bind=_engine_sunsheen)


class Database_session_sunsheen:
    def __enter__(self):
        self.session = _Session_sunsheen()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()


if __name__ == '__main__':
    with Database_session() as session:
        result = session.query(Device).filter_by(id=1).first().device_configs
