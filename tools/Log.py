#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
    @copyright: BHYN
    @license: private
    @author: km_xu
    @contact: Annlix@outlook.com
    @file: Log
    @project: tabocco_data_server
    @date: 2021-01-08 14:25:44 UTC+0800 1610087144
    @notice: This software is NOT open source.
"""

import os
import logging


class Log:
    def __init__(self, port=8888):
        self.log_filename = os.path.join(os.getcwd(), 'logs', f"tabocco_data_server:{port}.log")
        logging.basicConfig(filename=self.log_filename, filemode='a', level=0)
        timed_handler = self.get_timed_logging_handler()
        formatter = self.get_formatter()
        timed_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        logger.addHandler(timed_handler)
    
    def get_timed_logging_handler(self):
        return logging.handlers.TimedRotatingFileHandler(filename=self.log_filename, when='D', interval=1)

    def get_formatter(self):
        fmt_str = "[%(asctime)s]{File:\"%(filename)s\",line:%(lineno)s}%(levelname)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S %z"
        return logging.Formatter(fmt=fmt_str, datefmt=datefmt)
