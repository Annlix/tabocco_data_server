#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import time
import upyun
import logging
sys.path.append('../')
from commons import macro
from redis_cache import producer

BUCKET = macro.UPYUN_BUCKET
USERNAME = macro.UPYUN_USERNAME
PASSWORD = macro.UPYUN_PASSWORD

def save_to_upyun(data):
    try:
        res = None
        image_data = data['data']
        url_key = list((image_data.keys()))[0]
        image_localpath = list(image_data.values())[0]['value']
        image_localpath_components = image_localpath.split('/')
        upyun_save_path = "/%s/%s"%(image_localpath_components[-2],
            image_localpath_components[-1])
        up = upyun.UpYun(BUCKET, username = USERNAME, password = PASSWORD,
            timeout = 30, endpoint = upyun.ED_AUTO)
        if os.path.exists(image_localpath):
            with open(image_localpath, 'rb') as f:
                res = up.put(upyun_save_path, f)
                print(res)
    except upyun.UpYunServiceException as se:
        print('Except an UpYunServiceException ...')
        logging.info('Except an UpYunServiceException ...')
        print('Request Id: ' + se.request_id)
        logging.info('Request Id: ' + se.request_id)
        print('HTTP Status Code: ' + str(se.status))
        logging.info('HTTP Status Code: ' + str(se.status))
        print('Error Message:    ' + se.msg + '\n')
        logging.info('Error Message:    ' + se.msg + '\n')
    except upyun.UpYunClientException as ce:
        print('Except an UpYunClientException ...')
        logging.info('Except an UpYunClientException ...')
        print('Error Message: ' + ce.msg + '\n')
        logging.info('Error Message: ' + ce.msg + '\n')
    except Exception as e:
        logging.info(e)
        print(e)
    finally:
        # if upload operation error ocurred ,insert image info into redis again
        if res == None:
            # producer.insert_into_redis(data, macro.REDIS_LIST_KEY)
            return False
        else:
            # delete local image file
            command = "rm -f %s"%(image_localpath)
            if os.path.exists(image_localpath):
                os.system(command)
            # replace local path with remote path
            data['data'][url_key]['value'] = upyun_save_path
            return True
