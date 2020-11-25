#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import tornado
import logging
import argparse
from tools import *
from commons.macro import *
from services import *
from redis_cache import producer, email_producer
from tornado import gen, ioloop, stack_context
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import asyncio
import demjson

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# def handler_exception(handle_func):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kw):
#         	try:
#         		func(*args, **kw)
#         	except Exception as e:
#         		print(e)
#         		print('wrappers')
#         		handle_func()
#         return wrapper
#     return decorator

class DataCollectionServer(TCPServer):
    def __init__(self, io_loop=None, **kwargs):
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        TornadoTCPConnection(stream, address, io_loop=self.io_loop)


class TornadoTCPConnection(object):
    MAX_SIZE = 10 * 1024  # 10KB
    MAX_WORKERS = 10
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def __init__(self, stream, address, io_loop):
        self.count = 0
        self.json_request = {}
        self.data_cache = {}
        self.stream = stream
        self.address = address
        self.io_loop = io_loop
        self.address_string = '{}:{}'.format(address[0], address[1])
        logging.info('connected from %s' % (self.address_string))
        self.clear_request_state()
        self.stream.set_close_callback(stack_context.wrap(self.on_connection_close))
        self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + TCP_CONNECTION_TIMEOUT,
                                                       stack_context.wrap(self.on_timeout))
        self.stream.read_bytes(num_bytes=TornadoTCPConnection.MAX_SIZE,
                               callback=stack_context.wrap(self.on_message_receive), partial=True)

    def wait_new_request(self):
        self.stream.read_bytes(num_bytes=TornadoTCPConnection.MAX_SIZE,
                               callback=stack_context.wrap(self.on_message_receive), partial=True)

    # call back
    # def wait_push_data_request(self):
    # 	self.stream.read_bytes(num_bytes = self.json_request['size'], callback=stack_context.wrap(self.on_message_receive), partial=False)

    def on_timeout(self):
        self.close()
        logging.info('{} connection timeout.'.format(self.address_string))

    @email_producer.email_wrapper
    def on_message_receive(self, data):
        try:
            data_str = native_str(data.decode('UTF-8'))
            logging.info(data_str)
            print(data_str)
            # tmp = json.loads(data_str)
            tmp = demjson.decode(data_str)
            for k, v in tmp.items():
                self.json_request[k] = v
            if self.json_request.__contains__('method'):
                email_producer.insert_into_redis(data_str, EMAIL_REDIS_LIST_KEY)
                request = self.json_request['method']
                # if request == 'push_data':
                # 	self.on_push_data_request(self.json_request)
                # elif request == 'push_data_size':
                # 	print('here in push_data_size')
                # 	self.on_push_data_size_request()
                # elif request == 'pull_param':
                # 	self.on_pull_param_request(self.json_request)
                # elif request == 'push_image':
                # 	logging.info('push_image')
                # 	self.on_push_image_request(self.json_request)
                # elif request == 'param_updated':
                # 	logging.info('param_updated')
                # 	self.close()
                # elif request == 'close_connection':
                # 	logging.info('close_connection')
                # 	self.close()
                if request == 'push_data':
                    self.on_push_data_request(self.json_request)
                elif request == 'push_data_size':
                    print('here in push_data_size')
                    self.on_push_data_size_request()
                elif request == 'pull_param':
                    logging.info('pull_param')
                    self.on_pull_param_request(self.json_request)
                elif request == 'push_image':
                    # print('push_image')
                    logging.info('push_image')
                    self.on_push_image_request(self.json_request)
                elif request == 'update_device_info':
                    self.on_update_device_info_request()
                elif request == 'update_time':
                    self.on_update_time_request(self.json_request)
                elif request == 'param_updated':
                    self.handle_param_updated(self.json_request)
                elif request == 'close_connection':
                    self.handle_close_connection(self.json_request)
            else:
                self.on_error_request()
        except Exception as e:
            logging.info(e)
            print(e)
            self.on_error_request()
            raise e

    # directly call
    def on_push_data_size_request(self):
        self.stream.write(str.encode(get_reply_json(self.json_request)),
                          callback=stack_context.wrap(self.wait_push_data_request))

    # directly call
    def on_push_data_request(self, request):
        # add the redis part
        redis_data_key = str(request['device_id']) + '-data'
        for ts, data in request['package'].items():
            data_t = get_data_to_save(request, ts, data)
            logging.info(data_t)
            producer.set_redis(data_t, redis_data_key)
            producer.insert_into_redis(data_t, REDIS_LIST_KEY)
        # self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(self.wait_new_request))
        self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))

    # directly call
    @run_on_executor
    def on_pull_param_request(self, request):
        param = get_latest_device_config_json(request['device_id'])
        logging.info("param:\n")
        logging.info(param)
        if param:
            print(len(str.encode(param)))
            self.stream.write(str.encode(param), callback=stack_context.wrap(self.wait_push_param_reply))
        else:
            self.on_error_request()

    # call back
    def receiving_data(self, data):
        data_str = native_str(data.decode('UTF-8'))
        data_dict = convert_request_to_dict(data_str)
        if data_dict == None:
            self.on_error_request()
        else:
            if data_dict.__contains__('method'):
                self.json_request['method'] = data_dict['method']
                self.stop_receiving_data()
            else:
                self.count += 1
                user_define_key = ''
                for k, v in data_dict.items():
                    if k != 'ts':
                        user_define_key = k
                if self.data_cache['package'].__contains__(data_dict['ts']):
                    self.data_cache['package'][data_dict['ts']][user_define_key] = {'value': data_dict[user_define_key]}
                else:
                    self.data_cache['package'][data_dict['ts']] = {}
                    self.data_cache['package'][data_dict['ts']][user_define_key] = {'value': data_dict[user_define_key]}
                self.stream.read_bytes(num_bytes=TornadoTCPConnection.MAX_SIZE,
                                       callback=stack_context.wrap(self.receiving_data), partial=True)

    # directly call
    def on_push_image_request(self, request):
        num_bytes = self.json_request['size']
        if isinstance(num_bytes, int) and num_bytes > 0:
            self.stream.write(str.encode(get_reply_json(self.json_request)),
                              callback=stack_context.wrap(self.start_receive_image_data))
        else:
            self.on_error_request()

    # directly call
    def handle_push_image(self, request):
        print(request['method'])
        self.stream.write(str.encode(get_reply_string(self.json_request)),
                          callback=stack_context.wrap(self.start_receiving_image))

    # call back
    def start_receive_image_data(self):
        self.json_request['method'] = 'pushing_image'
        # print('start_receive_image_data')
        logging.info('start_receive_image_data')
        logging.info('size:' + str(self.json_request['size']))
        self.stream.read_bytes(num_bytes=self.json_request['size'],
                               callback=stack_context.wrap(self.on_image_upload_complete), partial=False)

    # call back
    @run_on_executor
    @email_producer.email_wrapper
    def on_image_upload_complete(self, data):
        logging.info('here in on_image_upload_complete')
        try:
            filepath = check_device_img_file(self.json_request['device_id'])
            url = get_image_url_local(filepath, self.json_request['ts'])
            # url = get_image_url_local(filepath, self.json_request['acquisition_time'])
            save_image_local(data, url)
            self.json_request['image_info'] = {self.json_request['key']: {'value': url}}
            tmp_data = get_image_info_to_save(self.json_request)
            producer.set_redis(tmp_data, str(self.json_request['device_id']) + '-image')
            if producer.insert_into_redis(tmp_data, REDIS_LIST_KEY):
                self.stream.write(str.encode(get_reply_string(self.json_request)),
                                  callback=stack_context.wrap(self.wait_new_request))
            else:
                self.on_error_request()
        except Exception as e:
            logging.info(e)
            self.on_error_request()
            raise e

    # directly call
    def on_update_device_info_request(self, request):
        self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))

    # directly call
    def on_update_time_request(self, request):
        self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))

    def on_error_request(self):
        self.stream.write(str.encode(get_reply_string(is_failed=True)), callback=stack_context.wrap(self.close))

    def clear_request_state(self):
        self._close_callback = None

    def set_close_callback(self, callback):
        self._close_callback = stack_context.wrap(callback)

    def on_connection_close(self):
        if self.timeout_handle is not None:
            self.io_loop.remove_timeout(self.timeout_handle)
            self.timeout_handle = None
        if self._close_callback is not None:
            callback = self._close_callback
            self._close_callback = None
            callback()
        self.clear_request_state()
        logging.info("{}: disconnect".format(self.address_string))

    def close(self):
        self.stream.close()


def main():
    parser = argparse.ArgumentParser(description='custom_tcp_server')
    parser.add_argument('-p', '--port', type=int,
                        help='port to listen')
    args = parser.parse_args()
    if args.port is None:
        args.port = 8888
    # logging.basicConfig(level=logging.INFO)
    # log = logging.getLogger()
    # log.addHandler(get_log_file_handler("port:" + str(args.port) + ".log"))
    server = DataCollectionServer()
    server.listen(args.port)
    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    try:
        initialize_service_bash()
        main()
    except Exception as e:
        logging.info("ocurred Exception: %s" % str(e))
        # print ("ocurred Exception: %s" % str(e))
        quit()
