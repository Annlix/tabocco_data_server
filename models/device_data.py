#!/usr/bin/env python   
# -*- coding:utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, DECIMAL, ENUM, JSON
import sys

sys.path.append('../')
from models import Base

'''
device_data
id int 10 primary key
device_config_id int 10
device_id int 10
data json
ts timestamp nullable
updated_at timestamp
created_at timestamp
deleted_at timestamp nullable
null nullable
'''


class Device_data(Base):
    __tablename__ = 'device_data'

    id = Column(INTEGER(display_width=10), primary_key=True)
    # device_id = Column(INTEGER(display_width = 10))
    data = Column(JSON)
    ts = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)
    type = Column(VARCHAR, nullable=False)

    device_config_id = Column(INTEGER(display_width=10), ForeignKey('device_config.id'))
    device_config = relationship('Device_config', back_populates='device_datas')

    device_id = Column(INTEGER(display_width=10), ForeignKey('device.id'))
    device = relationship('Device', back_populates='device_datas')

    def __repr__(self):
        return f"<{self.__class__.__name__}>(table={self.__tablename__}, id={self.id}, data={self.data}, ts={self.ts}, updated_at={self.updated_at}, created_at={self.created_at}, deleted_at={self.deleted_at}, type={self.type}, device_id={self.device_id}, device_config_id={self.device_config_id})"
