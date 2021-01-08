#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import argparse
import demjson
import traceback

class TestClient():
    menus = ["quit", "push_data", "push_data_size", "pull_param", "push_image", "update_device_info", "update_time", "param_updated", "close_connection"]
    default_messages = dict(quit="{}", push_data = "{'device_id': 4, 'device_config_id': 1572, 'package': {'1606979815': {'temp': 20, 'humidity': 30, 'soil_temp': 2.3},'1606979816': {'temp': 20, 'humidity': 30, 'soil_temp': 2.3}}}", push_data_size = "{}", push_image = "{}", update_device_info = "{}", update_time = "{}", param_updated = "{}", close_connection = "{}")
    
    def __init__(self, args):
        self.config = vars(args)
        if self.config['method'] is None:
            menu = self.get_menu_choice()
            if menu == 0 or menu == 'quit' :
                exit()
            self.config['method'] = menu
        self.connect()
        self.send_message()
        response = ""
        while True:
            rep = self.sock.recv(16)
            if len(rep) == 0:
                break
            response += rep.decode("utf-8")
        print("Recv:", response)

    def connect(self):
        self.sock = socket.create_connection((self.config['host'], self.config['port']), timeout = 60)
        
    
    def send_message(self):
        data = self.get_to_send_message()
        data = demjson.encode(data, 'utf-8')
        print("Send:", data)
        self.sock.send(data)
    
    def get_to_send_message(self):
        data = input("Please input the data which you desired to send to server:\n")
        if len(data) != 0:
            data = demjson.decode(data, encoding='utf-8')
        else:
            data = demjson.decode(self.default_messages[self.config['method']])
        data = dict({"method": self.config['method']}, **data)
        return data
    
    def show_menu(self):
        menu_str = ""
        for item in self.menus:
            index = self.menus.index(item)
            menu_str += f"[{index}] {item}\t"
        print(menu_str)
    
    def get_menu_choice(self):
        print("Please choose a method:")
        self.show_menu()
        choice = input("Enter 1-8, 0 to quit:\n")
        choice = int(choice)
        if choice < 0 or choice > 8:
            choice = 0
        choice = self.menus[choice]
        return choice
    
    def get_default_message(self, method):
        return self.default_messages[method]
    

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--host',
                            type=str,
                            help="The server host",
                            default="127.0.0.1")
        parser.add_argument('--port',
                            type=int,
                            help="The server port",
                            default=8888)
        parser.add_argument('--method',
                            type=str,
                            help="The request method",
                            default=None,
                            choices=["push_data", "push_data_size", "pull_param", "push_image", "update_device_info", "update_time", "param_updated", "close_connection"])
        args = parser.parse_args()
        TestClient(args)
    except Exception as e:
        traceback.print_exc()
