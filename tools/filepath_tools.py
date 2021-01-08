#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import os

# should be called in the project root catalog
def check_device_img_file(device_id, create_if_nonexists = True):
	if not isinstance(device_id, str):
		device_id = str(device_id)
	filepath = os.path.abspath('./images/%s'%(device_id))
	if not os.path.exists(filepath):
		if create_if_nonexists:
			os.mkdir(filepath)
	return filepath

def get_image_url_local(filepath, image_acquisition_time):
	url = os.path.join(filepath, '%s.jpg'%(str(image_acquisition_time)))
	return url

def get_image_url_server():
	pass

if __name__ == '__main__':
	filepath = check_device_img_file(3, create_if_nonexists = False)
	url = get_image_url_local(filepath, 123)