#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse
from tools import *
from commons.macro import *
from services import *
from redis_cache import producer, email_producer
from tornado import gen, ioloop
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
from tornado.ioloop import IOLoop
import traceback

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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
        logging.info(f'Connected from {self.address_string}')
        self.clear_request_state()
        self.stream.set_close_callback(self.close_callback)

    def close_callback(self):
        print("The connection have been closed.")

    async def get_request(self):
        data = await self.stream.read_bytes(num_bytes=TornadoTCPConnection.MAX_SIZE, partial=True)
        await self.on_message_receive(data)

    async def wait_new_request(self):
        data = await self.stream.read_bytes(num_bytes=TornadoTCPConnection.MAX_SIZE)
        await self.on_message_receive(data)

    def on_timeout(self):
        self.close()
        logging.info('{} connection timeout.'.format(self.address_string))

    @email_producer.email_wrapper
    async def on_message_receive(self, data):
        try:
            data_str = data.decode('utf-8')
            logging.info(f"Received: {data_str}")
            print(">>>>>> RECV", data_str, "======", sep="\n")
            tmp = json.loads(data_str, strict=False)
            for k, v in tmp.items():
                self.json_request[k] = v
            if 'method' in self.json_request:
                email_producer.insert_into_redis(data_str, EMAIL_REDIS_LIST_KEY)
                request = self.json_request['method']
                if request == 'update_time':
                    await self.on_update_time_request(self.json_request)
                elif request == 'pull_param':
                    await self.on_pull_param_request(self.json_request)
                elif request == 'push_data':
                    await self.on_push_data_request(self.json_request)
                elif request == 'push_data_size':
                    await self.on_push_data_size_request(self.json_request)
                elif request == 'push_image':
                    await self.on_push_image_request(self.json_request)
                elif request == 'update_device_info':
                    await self.on_update_device_info_request(self.json_request)
                # elif request == 'param_updated':
                #     self.handle_param_updated(self.json_request)
                # elif request == 'close_connection':
                #     self.handle_close_connection(self.json_request)
            else:
                self.on_error_request()
        except Exception as e:
            logging.info(e)
            traceback.print_exc()
            await self.on_error_request()
            raise e
    
    def validate_update_time_request(self, request):
        return isinstance(request, dict) and \
               'method' in request and \
               request['method'] == 'update_time'

    async def on_update_time_request(self, request):
        if self.validate_update_time_request(request):
            reply = get_reply_json(request)
            if isinstance(reply, str):
                reply = reply.encode('utf-8')
            print("<<<<<< SEND", reply, sep='\n')
            await self.stream.write(reply)
            self.close()
        else:
            await self.on_error_request()

    # directly call
    async def on_push_data_size_request(self, request):
        response = get_reply_json(request)
        if isinstance(response, str):
            response = response.encode("utf-8")
        print("<<<<<< SEND", response, sep='\n')
        await self.stream.write(response)
        self.close()

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
            # Check the device is exists
            device_id = int(request['device_id'])
            device_info = utils.check_device_exists(device_id)
            if device_info != False:
                redis_data_key = f"{device_id}-data"
                for ts, data in request['package'].items():
                    data_t = get_data_to_save(request, ts, data)
                    logging.info(data_t)
                    producer.set_redis(data_t, redis_data_key)
                    producer.insert_into_redis(data_t, REDIS_LIST_KEY)
                    reply = get_reply_json(self.json_request)
                if isinstance(reply, str):
                    reply = reply.encode("utf-8")
                print("<<<<<< SEND", reply, sep='\n')
                await self.stream.write(reply)
                self.close()
            else:
                await self.on_error_request(msg="The device is not exists")
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
            if param:
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
    async def on_push_image_request(self, request):
        print(request)
        num_bytes = request['size']
        if isinstance(num_bytes, int) and num_bytes > 0:
            response = get_reply_json(request)
            if isinstance(response, str):
                response = response.encode("utf-8")
            print("<<<<<< SEND", response, sep='\n')
            await self.stream.write(response)
            await self.start_receive_image_data()
        else:
            self.on_error_request()

    # directly call
    def handle_push_image(self, request):
        self.stream.write(str.encode(get_reply_string(self.json_request)),
                          callback=stack_context.wrap(self.start_receiving_image))

    # call back
    async def start_receive_image_data(self):
        self.json_request['method'] = 'pushing_image'
        logging.info('start_receive_image_data')
        logging.info('size:' + str(self.json_request['size']))
        img_data = await self.stream.read_bytes(num_bytes=self.json_request['size'])
        await self.on_image_upload_complete(img_data)

    # call back
    # @email_producer.email_wrapper
    async def on_image_upload_complete(self, data):
        try:
            filepath = check_device_img_file(self.json_request['device_id'])
            url = get_image_url_local(filepath, self.json_request['ts'])
            save_image_local(data, url)
            self.json_request['image_info'] = {self.json_request['key']: {'value': url}}
            tmp_data = get_image_info_to_save(self.json_request)
            producer.set_redis(tmp_data, str(self.json_request['device_id']) + '-image')
            if producer.insert_into_redis(tmp_data, REDIS_LIST_KEY):
                response = get_reply_string(self.json_request)
                if isinstance(response, str):
                    response = response.encode('utf-8')
                print("<<<<<< SEND", response, sep='\n')
                await self.stream.write(response)
                self.close()
            else:
                await self.on_error_request()
        except Exception as e:
            logging.info(e)
            await self.on_error_request()
            raise e

    # directly call
    async def on_update_device_info_request(self, request):
        response = get_reply_json(request)
        if isinstance(response, str):
            response = response.encode('utf-8')
        await self.stream.write(response)
        self.close()
        # self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))

    async def on_error_request(self, msg = None):
        response = get_reply_json(None, is_failed=True, msg=msg)
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
    Log(port=args.port)
    msg = f"Start the server on 127.0.0.1:{args.port}"
    logging.info(msg)
    print(msg)
    loop = IOLoop.current()
    server = DataCollectionServer()
    server.listen(args.port)
    logging.info("Server is running...")
    loop.start()


if __name__ == "__main__":
    try:
        logging.info("Server starting...")
        initialize_service_bash()
        main()
    except KeyboardInterrupt:
        logging.warn("Exit by ^C")
        print("Exit by ^C")
        quit()
    except Exception as e:
        traceback.print_exc()
        logging.info("occurred Exception: %s" % str(e))
        quit()
