#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
    @copyright: BHYN
    @license: private
    @author: km_xu
    @contact: Annlix@outlook.com
    @file: aliyun_tools
    @project: tabocco_data_server
    @date: 2020-12-30 16:21:48 UTC+0800 1609316508
    @notice: This software is NOT open source.
"""

from commons.macro import *
import oss2
import sys
import os
import logging

class AliyunOss:
    def __init__(self):
        try:
            self.auth = oss2.Auth(aliyun_oss['access_key'], aliyun_oss['access_secret'])
            self.bucket = oss2.Bucket(self.auth, aliyun_oss['endpoint_uri'], aliyun_oss['bucket'])
        except oss2.exceptions.ClientError as e:
            print("ClientError", e)
            logging.error(e)
        except oss2.exceptions.RequestError as e:
            print("RequestError", e)
            logging.error(e)
        except oss2.exceptions.ServerError as e:
            print("ServerError", e)
            logging.error(e)

    @classmethod
    def upload_image(cls, data:dict):
        try:
            alioss = cls()
            for image_key in data['data']:
                image_value = data['data'][image_key]['value']
                image_value = image_value[1:]
                image_path = os.path.abspath(os.path.join(os.getcwd(), '..', 'images', image_value))
                with open(image_path, "rb") as fp:
                    file_content = fp.read()
                res = alioss.bucket.put_object(image_value, file_content)
                return True
        except oss2.exceptions.ClientError as e:
            print("ClientError", e)
            logging.error(e)
            return False
        except oss2.exceptions.RequestError as e:
            print("RequestError", e)
            logging.error(e)
            return False
        except oss2.exceptions.ServerError as e:
            print("ServerError", e)
            logging.error(e)
            return False
