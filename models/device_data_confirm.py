#!/usr/bin/env python   
# -*- coding:utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, DECIMAL, ENUM, JSON
import sys

sys.path.append('../')
from models import Base

'''
    id INT UNSIGNED auto_increment NOT NULL,
	source_device_id INT UNSIGNED NOT NULL COMMENT '原始设备编号-设备上传的设备编号',
	source_config_id INT UNSIGNED NOT NULL COMMENT '原始设备配置编号-设备上传的设备配置编号',
	new_device_id INT UNSIGNED NULL COMMENT '新的设备编号-如果匹配到',
	new_config_id INT UNSIGNED NULL COMMENT '新的配置编号-如果匹配到',
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL,
	updated_at TIMESTAMP NULL,
	deleted_at TIMESTAMP NULL,
	`data` json NULL COMMENT '待存入的数据',
    `ts` timestamp NULL DEFAULT NULL,
	extra_data varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '一些额外的数据',
	CONSTRAINT device_data_confirm_pk PRIMARY KEY (id),
	CONSTRAINT device_data_confirm_FK_1 FOREIGN KEY (new_config_id) REFERENCES thcpn2.device_config(id),
	CONSTRAINT device_data_confirm_FK FOREIGN KEY (new_device_id) REFERENCES thcpn2.devices(id)
'''

class Device_data_confirm(Base):
    __tablename__ = 'device_data_confirm'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
    source_device_id = Column(INTEGER(unsigned=True), nullable=False, comment="原始设备编号-设备上传的设备编号")
    source_config_id = Column(INTEGER(unsigned=True), nullable=False, comment="原始设备配置编号-设备上传的设备配置编号")
    new_device_id = Column(INTEGER(unsigned=True), nullable=True, comment="新的设备编号-如果匹配到")
    new_config_id = Column(INTEGER(unsigned=True), nullable=True, comment="新的配置编号-如果匹配到")
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    data = Column(JSON)
    ts = Column(TIMESTAMP, nullable=True)
    extra_data = Column(VARCHAR(length=512))
    updated_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)

    # new_device_id = Column(INTEGER(), ForeignKey('device.id'))
    # device = relationship('Device', back_populates='device_datas')

    # new_config_id = Column(INTEGER(display_width=10), ForeignKey('device_config.id'))
    # device_config = relationship('Device_config', back_populates='device_datas')
