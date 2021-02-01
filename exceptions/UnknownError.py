#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

class UnknownError(Exception):
    def __init__(self, message: str = "Some error occurred in server."):
        self.message = message