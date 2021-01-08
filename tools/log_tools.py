#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler

def get_log_file_handler(filename_prefix=None):
    if filename_prefix is None:
        filename_prefix = 'tabocco_data_server'
    fmt_str = "[%(asctime)s]{File:\"%(filename)s\",line:%(lineno)s}%(levelname)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S %z"
    formatter = logging.Formatter(fmt=fmt_str, datefmt=datefmt)
    log_file_handler = TimedRotatingFileHandler(filename=filename_prefix, when="D", interval=1, backupCount=0)
    log_file_handler.setLevel(0)
    log_file_handler.setFormatter(formatter)
    return log_file_handler
