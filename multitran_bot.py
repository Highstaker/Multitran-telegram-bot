#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#TODO
#-translate the bot to other languages
#-make donation info
#-fix flags of languages in both help message and pick menu

VERSION_NUMBER = (0,4,0)

import logging
import telegram
from time import time, sleep
from os import path, listdir, walk
import socket
import pickle #module for saving dictionaries to file
from bs4 import BeautifulSoup #HTML parser
import re

from webpage_reader import getHTML_specifyEncoding

#if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

logging.basicConfig(format = u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s', 
	level = logging.WARNING)


############
##PARAMETERS
############

#A filename of a file containing a token.
TOKEN_FILENAME = 'token'

#A path where subscribers list is saved.
SUBSCRIBERS_BACKUP_FILE = '/tmp/multitran_bot_subscribers_bak'

#Maximum amount of characters per message
MAX_CHARS_PER_MESSAGE = 2000

#Indicies that correspond to various languages on Multitran
LANGUAGE_INDICIES = {
"🇬🇧 English" :1
, "🇩🇪 Deutsch":3
, "🇫🇷 Français":4
, "🇪🇸 Español":5
, "🇮🇹 Italiano":23
, "🇪🇴 Esperanto":34
, "🇳🇱 Nederlands":24
, "🇱🇻 Latvian":27
, "🇪🇹 Estonian":26
, "🇦🇫 Afrikaans":31
, "🇽🇦🇱 Kalmyk":35
}

#########
####BUTTONS
##########

HELP_BUTTON = "⁉️" + "Help"
PICK_LANGUAGE_BUTTON = "🇬🇧🇫🇷🇮🇹🇩🇪🇳🇱🇪🇸 Pick Language"
BACK_BUTTON = "⬅️ Back"
ABOUT_BUTTON = "ℹ️ About"
RATE_ME_BUTTON = "⭐️ Like me? Rate!"

##############
####MESSAGES
############

HELP_MESSAGE = '''
This bot connects to Multitran dictionary to translate between Russian and a selected language.
By default it is set to English.
To translate a word, type it.
To change language click the \" ''' + PICK_LANGUAGE_BUTTON + ''' \" button.

Available languages are: ''' + ", ".join(list(LANGUAGE_INDICIES.keys())) + '''
'''

ABOUT_MESSAGE = """*Multitran Bot*
_Created by:_ Highstaker a.k.a. OmniSable. 
Get in touch with me on Telegram if you have questions, suggestions or bug reports (@OmniSable).
Source code can be found [here](https://github.com/Highstaker/Multitran-telegram-bot).
Version: """ + ".".join([str(i) for i in VERSION_NUMBER]) + """

This bot uses the [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot) library.

Translation data is received from [Multitran online dictionary](multitran.ru).
"""

START_MESSAGE = "Welcome! Type /help to get help."

RATE_ME_MESSAGE = """
You seem to like this bot. You can rate it [here](https://storebot.me/bot/multitran_bot)!

Your ⭐️⭐️⭐️⭐️⭐️ would be really appreciated!
"""

def split_list(alist,max_size=1):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(alist), max_size):
		yield alist[i:i+max_size]

MAIN_MENU_KEY_MARKUP = [[PICK_LANGUAGE_BUTTON],[HELP_BUTTON,ABOUT_BUTTON,RATE_ME_BUTTON]]
LANGUAGE_PICK_KEY_MARKUP = list(  split_list( list(LANGUAGE_INDICIES.keys()) ,3)  ) + [[BACK_BUTTON]]

################
###GLOBALS######
################

with open(path.join(path.dirname(path.realpath(__file__)), TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

#############
##METHODS###
############


###############
###CLASSES#####
###############

class TelegramBot():
	"""The bot class"""

	LAST_UPDATE_ID = None

	#{chat_id: [LANGUAGE_INDEX], ...}
	subscribers = {}

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		#get list of all image files
		self.loadSubscribers()

	def loadSubscribers(self):
		'''
		Loads subscribers from a file
		'''
		try:
			with open(SUBSCRIBERS_BACKUP_FILE,'rb') as f:
				self.subscribers = pickle.load(f)
				print("self.subscribers",self.subscribers)
		except FileNotFoundError:
			logging.warning("Subscribers backup file not found. Starting with empty list!")

	def saveSubscribers(self):
		'''
		Saves a subscribers list to file
		'''
		with open(SUBSCRIBERS_BACKUP_FILE,'wb') as f:
			pickle.dump(self.subscribers, f, pickle.HIGHEST_PROTOCOL)

	def sendMessage(self,chat_id,text,key_markup=MAIN_MENU_KEY_MARKUP,preview=True):
		logging.warning("Replying to " + str(chat_id) + ": " + text)
		while True:
			try:
				if text:
					self.bot.sendChatAction(chat_id,telegram.ChatAction.TYPING)
					self.bot.sendMessage(chat_id=chat_id,
						text=text,
						parse_mode='Markdown',
						disable_web_page_preview=(not preview),
						reply_markup=telegram.ReplyKeyboardMarkup(key_markup)
						)
			except Exception as e:
				if "Message is too long" in str(e):
					self.sendMessage(chat_id=chat_id
						,text="Error: Message is too long!"
						)
					break
				if ("urlopen error" in str(e)) or ("timed out" in str(e)):
					logging.error("Could not send message. Retrying! Error: " + str(e))
					sleep(3)
					continue
				else:
					logging.error("Could not send message. Error: " + str(e))
					# self.sendMessage(chat_id=chat_id
					# 	,text="Unknown Error!"
					# 	)
			break

	def sendPic(self,chat_id,pic):
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				#set file read cursor to the beginning. This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				self.bot.sendChatAction(chat_id,telegram.ChatAction.UPLOAD_PHOTO)
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id,photo=pic)
			except Exception as e:
				logging.error("Could not send picture. Retrying! Error: " + str(e))
				continue
			break

	def getUpdates(self):
		'''
		Gets updates. Retries if it fails.
		'''
		#if getting updates fails - retry
		while True:
			try:
				updates = self.bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=3)
			except Exception as e:
				logging.error("Could not read updates. Retrying! Error: " + str(e))
				sleep(3)
				continue
			break
		return updates


	def echo(self):
		bot = self.bot

		updates = self.getUpdates()

		for update in updates:
			chat_id = update.message.chat_id
			Message = update.message
			from_user = Message.from_user
			message = Message.text
			logging.warning("Received message: " + str(chat_id) + " " + from_user.username + " " + message)

			#register the user if not present in the subscribers list
			try:
				self.subscribers[chat_id]
			except KeyError:
				self.subscribers[chat_id] = 1

			#I had no idea you could send an empty message
			try:
				if message:
					if message == "/start":
						self.sendMessage(chat_id=chat_id
							,text=START_MESSAGE
							)
					elif message == "/help" or message == HELP_BUTTON:
						self.sendMessage(chat_id=chat_id
							,text=HELP_MESSAGE
							)
					elif message == "/about" or message == ABOUT_BUTTON:
						self.sendMessage(chat_id=chat_id
							,text=ABOUT_MESSAGE
							)
					elif message == "/rate" or message == RATE_ME_BUTTON:
						self.sendMessage(chat_id=chat_id
							,text=RATE_ME_MESSAGE
							)
					elif message == PICK_LANGUAGE_BUTTON:
						self.sendMessage(chat_id=chat_id
							,text="Select language"
							,key_markup=LANGUAGE_PICK_KEY_MARKUP
							)
					elif message == BACK_BUTTON:
						self.sendMessage(chat_id=chat_id
							,text="Back to Main Menu"
							)
					elif message in list(LANGUAGE_INDICIES.keys()):
						#message is a language pick
						pass
						self.subscribers[chat_id] = LANGUAGE_INDICIES[message]
						self.sendMessage(chat_id=chat_id
							,text="Language is set to " + message
							)
					else:
						if message[0] == "/":
							message = message[1:]
						message = message.replace("_","").replace("*","").replace("`","")

						page_url = 'http://www.multitran.ru/c/m.exe?l1='+str(self.subscribers[chat_id]) +'&s=' + message
						page = getHTML_specifyEncoding(page_url, encoding='cp1251',method='replace')
						soup = BeautifulSoup(page)

						temp1 = [i for i in soup.find_all('table') if not i.has_attr('class') and not i.has_attr('id') and not i.has_attr('width') and i.has_attr('cellpadding') and i.has_attr('cellspacing') and i.has_attr('border') 
						and not len(i.find_all('table'))
						]

						def process_result(temp1):
							result = ""
							for tr in temp1.find_all('tr'):
								tds = tr.find_all('td')
								def translations_row():
									result = "`" + tr.find_all('a')[0].text + "`" + " "*5
									for a in tr.find_all('a')[1:]:
										if not 'i' in [i.name for i in a.children]:
											result +=  a.text.replace("_","").replace("*","").replace("`","") + "; "
									return result

								if tds[0].has_attr('bgcolor'):
									if tds[0]['bgcolor'] == "#DBDBDB":
										result += "\n" + "*" + tr.text.split("|")[0].replace(tr.find_all('em')[0].text if tr.find_all('em') else "","").replace("в начало","").replace("\n","").replace("_","").replace("*","") + "*" + ( ( " "*5 + "_" + tr.find_all('em')[0].text  + "_") if tr.find_all('em') else "" )
									else:
										result += translations_row()
								else:
									result += translations_row()
								result += "\n"
							return result



						result=""
						#maybe the request is in Russian?
						if not len(temp1):
							page_url = 'http://www.multitran.ru/c/m.exe?l1=2&l2='+ str(self.subscribers[chat_id]) + '&s=' + message
							page = getHTML_specifyEncoding(page_url, encoding='cp1251',method='replace')
							soup = BeautifulSoup(page)

							temp1 = [i for i in soup.find_all('table') if not i.has_attr('class') and not i.has_attr('id') and not i.has_attr('width') and i.has_attr('cellpadding') and i.has_attr('cellspacing') and i.has_attr('border') and not len(i.find_all('table'))]

							# Maybe there is no such word?
							if not len(temp1):
								result="*Word not found!*"
								varia = soup.find_all('td',string=re.compile("Варианты"))
								print("varia",varia)
								if varia:
									logging.warning("Есть варианты замены!")
									# print(varia[0].find_next_sibling("td").find_all('a'))
									# quit()
									result += "\n" + "*Possible replacements: *" + varia[0].find_next_sibling("td").text

							else:
								#request is in Russian
								temp1= temp1[0]
								result = process_result(temp1)

						else:
							#request is in foreign language
							temp1= temp1[0]
							result = process_result(temp1)

						result += "\nLink to the dictionary page: " + page_url.replace(" ","+")

						result += "\nCurrent language is " + list(LANGUAGE_INDICIES.keys())[list(LANGUAGE_INDICIES.values()).index(self.subscribers[chat_id]) ]

						#break the result in several messages if it is too big
						if len(result) < MAX_CHARS_PER_MESSAGE:
							try:
								self.sendMessage(chat_id=chat_id
									,text=str(result)
									,preview=False
									)
							except Exception as e:
								logging.error("Could not process message. Error: " + str(e))
						else:
							result_split = result.split("\n")
							result = ""
							while result_split:
								while True:
									if result_split:
										result += result_split.pop(0)+"\n"
									else:
										break

									if len(result) > MAX_CHARS_PER_MESSAGE:
										break

								if result:
									self.sendMessage(chat_id=chat_id
										,text=str(result)
										,preview=False
										)
									result = ""
			except Exception as e:
				logging.error("Message processing failed! Error: " + str(e))
			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1


def main():
	bot = TelegramBot(BOT_TOKEN)

	#main loop
	while True:
		bot.echo()

if __name__ == '__main__':
	main()