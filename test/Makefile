APP_NAME = TCPClient

CC = $(shell which gcc)
PWD = $(shell pwd)

SRC_PATH = $(PWD)/src
BIN_PATH = $(PWD)/bin
ENTRY = $(SRC_PATH)/client.c
DEPS = $(ENTRY)

CFLAGS = -Og
CFLAGS += -v

.PHONY:
client:
	$(CC) $(CFLAGS) $(DEPS) -o $(BIN_PATH)/$(APP_NAME)
debug:
	$(CC) $(CFLAGS) -g -Og $(DEPS) -o $(BIN_PATH)/$(APP_NAME)