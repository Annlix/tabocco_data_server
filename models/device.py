#!/usr/bin/env python   
# -*- coding:utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, DECIMAL, ENUM, JSON
import sys

sys.path.append('../')
from models import Base

'''
device
id int 10 primary key
station_id int 10
name varchar 50
type varchar 50
company varchar 50
model varchar 50
sn varchar 50
version varchar 50
updated_at timestamp
created_at timestamp
deleted_at timestamp nullable
null nullable
'''


class Device(Base):
    __tablename__ = 'device'

    id = Column(INTEGER(display_width=10), primary_key=True)
    name = Column(VARCHAR(length=50))
    type = Column(VARCHAR(length=50))
    company = Column(VARCHAR(length=50))
    model = Column(VARCHAR(length=50))
    sn = Column(VARCHAR(length=50))
    version = Column(VARCHAR(length=50))
    status = Column(ENUM('normal', 'abnormal'))
    updated_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)

    station_id = Column(INTEGER(display_width=10), ForeignKey('station.id'))
    station = relationship('Station', back_populates='devices')

    device_configs = relationship('Device_config', back_populates='device')

    device_datas = relationship('Device_data', back_populates='device')
