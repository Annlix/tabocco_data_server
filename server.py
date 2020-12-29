#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse
from tools import *
from commons.macro import *
from services import *
from redis_cache import producer, email_producer
# from tornado import gen, ioloop, stack_context
from tornado import gen, ioloop
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
from tornado.ioloop import IOLoop

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
    async def handle_stream(self, stream, address):
        server = TornadoTCPConnection(stream, address)
        await server.get_request()


class TornadoTCPConnection(object):
    MAX_SIZE = 10 * 1024  # 10KB
    MAX_WORKERS = 10
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def __init__(self, stream, address):
        self.count = 0
        self.json_request = {}
        self.data_cache = {}
        self.stream = stream
        self.address = address
        self.address_string = f'{address[0]}:{address[1]}'
        logging.info(f'connected from {self.address_string}')
        self.clear_request_state()
        self.stream.set_close_callback(self.close_callback)
        # self.stream.set_close_callback(stack_context.wrap(self.on_connection_close))
        # self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + TCP_CONNECTION_TIMEOUT,
        #                                                stack_context.wrap(self.on_timeout))

    def close_callback(self):
        print("The connection have been closed.")

    async def get_request(self):
        data = await self.stream.read_bytes(num_bytes=TornadoTCPConnection.MAX_SIZE, partial=True)
        await self.on_message_receive(data)
        # read_future.add_done_callback(self.on_message_receive)

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
    async def on_message_receive(self, data):
        try:
            data_str = data.decode('utf_8')
            logging.info(f"Receive: {data_str}")
            print(">>>>>>Receive", data_str, "======", sep="\n")
            tmp = json.loads(data_str)
            for k, v in tmp.items():
                self.json_request[k] = v
            # if self.json_request.__contains__('method'):
            if 'method' in self.json_request:
                email_producer.insert_into_redis(data_str, EMAIL_REDIS_LIST_KEY)
                request = self.json_request['method']
                # Upload the data
                if request == 'push_data':
                    await self.on_push_data_request(self.json_request)
                elif request == 'push_data_size':
                    print('here in push_data_size')
                    self.on_push_data_size_request()
                elif request == 'pull_param':
                    logging.info('pull_param')
                    await self.on_pull_param_request(self.json_request)
                elif request == 'push_image':
                    # print('push_image')
                    logging.info('push_image')
                    self.on_push_image_request(self.json_request)
                elif request == 'update_device_info':
                    await self.on_update_device_info_request()
                elif request == 'update_time':
                    await self.on_update_time_request(self.json_request)
                elif request == 'param_updated':
                    self.handle_param_updated(self.json_request)
                elif request == 'close_connection':
                    self.handle_close_connection(self.json_request)
            else:
                self.on_error_request()
        except Exception as e:
            logging.info(e)
            print(e)
            print(e.__traceback__.tb_frame.f_globals["__file__"], e.__traceback__.tb_lineno, e)
            self.on_error_request()
            raise e

    # directly call
    def on_push_data_size_request(self):
        self.stream.write(str.encode(get_reply_json(self.json_request)),
                          callback=stack_context.wrap(self.wait_push_data_request))

    def validate_push_data_request(self, request):
        return isinstance(request, dict) and \
               'method' in request and \
               request['method'] == 'push_data' and \
               'device_id' in request and \
               isinstance(request['device_id'], int) and \
               'device_config_id' in request and \
               isinstance(request['device_config_id'], int) and \
               'package' in request and \
               isinstance(request['package'], dict)

        # directly call

    async def on_push_data_request(self, request):
        if self.validate_push_data_request(request):
            # add the redis part
            redis_data_key = f"{request['device_id']}-data"
            for ts, data in request['package'].items():
                print(ts, data)
                data_t = get_data_to_save(request, ts, data)
                print("The data from get_data_to_save", data_t)
                logging.info(data_t)
                producer.set_redis(data_t, redis_data_key)
                producer.insert_into_redis(data_t, REDIS_LIST_KEY)
            # self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(
            # self.wait_new_request))
                reply = get_reply_json(self.json_request)
            if isinstance(reply, str):
                reply = reply.encode("utf-8")
            self.stream.write(reply)
            # self.stream.write(reply, callback=stack_context.wrap(self.wait_new_request))
        else:
            await self.on_error_request()

    def validate_pull_param_request(self, request):
        return isinstance(request, dict) and \
               'device_id' in request and \
               isinstance(request['device_id'], int) and \
               'method' in request and \
               'pull_param' == request['method']

    # directly call
    # @run_on_executor
    async def on_pull_param_request(self, request):
        if self.validate_pull_param_request(request):
            param = get_latest_device_config_json(request['device_id'])
            logging.info("param:\n")
            logging.info(param)
            if param:
                print(len(str.encode(param)))
                if isinstance(param, str):
                    param = param.encode('utf-8')
                await self.stream.write(param)
                self.close()
                # self.stream.write(str.encode(param), callback=stack_context.wrap(self.wait_push_param_reply))
            else:
                await self.on_error_request()
        else:
            await self.on_error_request()

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
    async def on_update_device_info_request(self, request):
        data = get_reply_json(self.json_request)
        print(data)
        # self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))

    def validate_update_time_request(self, request):
        return isinstance(request, dict) and \
               'method' in request and \
               request['method'] == 'update_time'

    # directly call
    async def on_update_time_request(self, request):
        if self.validate_update_time_request(request):
            reply = get_reply_json(request)
            if isinstance(reply, str):
                reply = reply.encode('utf-8')
            # self.stream.write(reply, callback=stack_context.wrap(self.close))
            await self.stream.write(reply)
            print("Prerare close connection")
            self.close()
        else:
            await self.on_error_request()

    async def on_error_request(self):
        response = get_reply_json(None, is_failed=True)
        if isinstance(response, str):
            response = response.encode("utf-8")
        await self.stream.write(response)
        self.close()

    def clear_request_state(self):
        self._close_callback = None

    def set_close_callback(self, callback):
        self._close_callback = stack_context.wrap(callback)

    def on_connection_close(self):
        if self.timeout_handle is not None:
            # self.io_loop.remove_timeout(self.timeout_handle)
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
    msg = f"Start the server on 127.0.0.1:{args.port}"
    logging.info(msg)
    print(msg)
    loop = IOLoop.current()
    server = DataCollectionServer()
    server.listen(args.port)
    loop.start()


if __name__ == "__main__":
    try:
        initialize_service_bash()
        main()
    except Exception as e:
        print(e.__traceback__.tb_frame.f_globals["__file__"], e.__traceback__.tb_lineno, e)
        logging.info("occurred Exception: %s" % str(e))
        print("occurred Exception: %s" % str(e))
        quit()
