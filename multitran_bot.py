#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import socket
import logging
from telegram.ext import Updater

from command_handler import UserCommandHandler
from textual_data import BOT_TOKEN

# if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
					level=logging.WARNING)


############
# METHODS###
############

def is_integer(s):
	"""
	If a string is an integer, returns True
	"""
	try:
		int(s)
		return True
	except ValueError:
		return False


###############
# CLASSES######
###############

class MultitranBot(object):
	"""docstring for MultitranBot"""

	def __init__(self, token):
		super(MultitranBot, self).__init__()
		self.token = token

		self.updater = Updater(token=token)
		self.dispatcher = dispatcher = self.updater.dispatcher

		self.command_handler = UserCommandHandler(dispatcher)

	def run(self):
		self.updater.start_polling()


def main():
	bot = MultitranBot(BOT_TOKEN)
	bot.run()


if __name__ == '__main__':
	main()
