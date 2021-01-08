#!/usr/bin/env python
# coding=utf-8

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import logging

import smtplib

import sys
sys.path.append('../')
from commons.macro import *
import traceback


def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))

def send_alert_email(alert_message):
	for receiver in EMAIL_RECEIVERS:
		try:
			message = MIMEText(alert_message, 'plain', 'utf-8')
			message['from'] = _format_addr('tobacco test server <%s>'%EMAIL_SENDER)
			message['to'] = _format_addr('developers <%s>'%receiver)
			message['Subject'] = Header('tobacco test server alert message', 'utf-8').encode()
			server = smtplib.SMTP_SSL('smtp.163.com', 465)
			# server.set_debuglevel(1)
			server.login(EMAIL_SENDER, EMAIL_SENDER_PASSWORD)
			server.sendmail(EMAIL_SENDER, receiver, message.as_string())
			server.quit()
			print('alert email send successfully')
		except Exception as e:
			traceback.print_exc()
			print('alert email send unsuccessfully')
			server.quit()