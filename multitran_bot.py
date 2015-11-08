#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#TODO
#-translate the bot to other languages
#-make donation info
#-fix flags of languages in both help message and pick menu

VERSION_NUMBER = (0,5,3)

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

#############
##METHODS###
############

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

HELP_BUTTON = {"EN" : "⁉️" + "Help", "RU": "⁉️" + "Помощь"}
PICK_LANGUAGE_BUTTON = {"EN" : "🇬🇧🇫🇷🇮🇹🇩🇪🇳🇱🇪🇸 Pick Dictionary Language", "RU": "🇬🇧🇫🇷🇮🇹🇩🇪🇳🇱🇪🇸 Выбор языка словаря" }
BACK_BUTTON = {"EN" : "⬅️ Back", "RU": "⬅️ Назад"}
ABOUT_BUTTON = {"EN" : "ℹ️ About", "RU": "ℹ️ О программе"}
RATE_ME_BUTTON = {"EN" : "⭐️ Like me? Rate!", "RU": "⭐️ Нравится бот? Оцени!"}
EN_LANG_BUTTON = "🇬🇧 EN"
RU_LANG_BUTTON = "🇷🇺 RU"

##############
####MESSAGES
############

HELP_MESSAGE = { "EN":'''
This bot connects to Multitran dictionary to translate between Russian and a selected language.
By default it is set to English.
To translate a word, type it.
To change language click the \" ''' + PICK_LANGUAGE_BUTTON["EN"] + ''' \" button.

Available languages are: ''' + ", ".join(list(LANGUAGE_INDICIES.keys())) + '''
'''
,"RU":'''
Этот бот может переводить слова и выражения с русского языка на иностранный и наоборот.

Чтобы перевести слово, просто введите его. Русское слово будет переведено на выбранный иностранный язык, а иностранное - на русский.

По умолчанию в качестве иностранного выставлен английский язык.
Чтобы изменить язык, нажмите кнопку \" ''' + PICK_LANGUAGE_BUTTON["RU"] + ''' \" и выберите язык в меню.
'''
}

ABOUT_MESSAGE = {"EN": """*Multitran Bot*
_Created by:_ Highstaker a.k.a. OmniSable. 
Get in touch with me on Telegram if you have questions, suggestions or bug reports (@OmniSable).
Source code can be found [here](https://github.com/Highstaker/Multitran-telegram-bot).
Version: """ + ".".join([str(i) for i in VERSION_NUMBER]) + """
[My channel, where I post development notes and update news](https://telegram.me/highstakerdev).

This bot uses the [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot) library.

Translation data is received from [Multitran online dictionary](multitran.ru).
"""
,"RU":"""*Multitran Bot*
_Автор:_ Highstaker a.k.a. OmniSable. 
По вопросам и предложениям обращайтесь в Телеграм (@OmniSable).
Исходный код [здесь](https://github.com/Highstaker/Multitran-telegram-bot).
Версия: """ + ".".join([str(i) for i in VERSION_NUMBER]) + """
[Мой канал, где я объявляю о новых версиях ботов](https://telegram.me/highstakerdev).

Этот бот написан на основе библиотеки [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

Переводы берутся из [словаря Мультитран](multitran.ru).
"""
}


START_MESSAGE = "Welcome! Type /help to get help."

RATE_ME_MESSAGE = {"EN": """
You seem to like this bot. You can rate it [here](https://storebot.me/bot/multitran_bot)!

Your ⭐️⭐️⭐️⭐️⭐️ would be really appreciated!
"""
,"RU": """
Нравится бот? Оцените его [здесь](https://storebot.me/bot/multitran_bot)!

Буду очень рад хорошим отзывам! 8)
⭐️⭐️⭐️⭐️⭐️ 
"""
}

LANGUAGE_IS_SET_TO_MESSAGE = {"EN": "Language is set to ", "RU":"Язык установлен на "}

SELECT_DICT_LANGUAGE_MESSAGE = {"EN": "Select language", "RU":"Выберите язык"}

BACK_TO_MAIN_MENU_MESSAGE = {"EN": "Back to Main Menu", "RU":"Вы вернулись в главное меню"}

WORD_NOT_FOUND_MESSAGE = {"EN": "*Word not found!*", "RU": "*Слово не найдено!*"}

POSSIBLE_REPLACEMENTS_MESSAGE = {"EN": "*Possible replacements: *", "RU": "*Варианты замены: *"}

LINK_TO_DICT_PAGE_MESSAGE = {"EN": "\nLink to the dictionary page: ", "RU": "\nСсылка на страницу словаря: " }

CURRENT_LANGUAGE_IS_MESSAGE = {"EN": "\nCurrent language is ", "RU": "\nВыбранный язык:" }

def split_list(alist,max_size=1):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(alist), max_size):
		yield alist[i:i+max_size]

MAIN_MENU_KEY_MARKUP = [[PICK_LANGUAGE_BUTTON],[HELP_BUTTON,ABOUT_BUTTON,RATE_ME_BUTTON],[EN_LANG_BUTTON,RU_LANG_BUTTON]]
LANGUAGE_PICK_KEY_MARKUP = list(  split_list( list(LANGUAGE_INDICIES.keys()) ,3)  ) + [[BACK_BUTTON]]

################
###GLOBALS######
################

with open(path.join(path.dirname(path.realpath(__file__)), TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")


###############
###CLASSES#####
###############

class TelegramBot():
	"""The bot class"""

	LAST_UPDATE_ID = None

	#{chat_id: [Language_of_bot,LANGUAGE_INDEX_of_dictionary], ...}
	subscribers = {}

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		#get list of all image files
		self.loadSubscribers()

	def languageSupport(self,chat_id,message):
		'''
		Returns a message depending on a language chosen by user
		'''
		if isinstance(message,str):
			result = message
		elif isinstance(message,dict):
			try:
				result = message[self.subscribers[chat_id][0]]
			except:
				result = message["EN"]
		elif isinstance(message,list):
			#could be a key markup
			result = list(message)
			for n,i in enumerate(message):
				result[n] = self.languageSupport(chat_id,i)
		else:
			result = " "
			
		# print(result)
		return result


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
		key_markup = self.languageSupport(chat_id,key_markup)
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
				self.subscribers[chat_id] = ["EN",1]

			#I had no idea you could send an empty message
			try:
				if message:
					if message == "/start":
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,START_MESSAGE)
							)
					elif message == "/help" or message == self.languageSupport(chat_id,HELP_BUTTON):
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,HELP_MESSAGE)
							)
					elif message == "/about" or message == self.languageSupport(chat_id,ABOUT_BUTTON):
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,ABOUT_MESSAGE)
							)
					elif message == "/rate" or message == self.languageSupport(chat_id,RATE_ME_BUTTON):
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,RATE_ME_MESSAGE)
							)
					elif message == self.languageSupport(chat_id,PICK_LANGUAGE_BUTTON):
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,SELECT_DICT_LANGUAGE_MESSAGE)
							,key_markup=LANGUAGE_PICK_KEY_MARKUP
							)
					elif message == self.languageSupport(chat_id,BACK_BUTTON):
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,BACK_TO_MAIN_MENU_MESSAGE)
							)
					elif message == RU_LANG_BUTTON:
						self.subscribers[chat_id][0] = "RU"
						self.sendMessage(chat_id=chat_id
							,text="Сообщения бота будут отображаться на русском языке."
							)
					elif message == EN_LANG_BUTTON:
						self.subscribers[chat_id][0] = "EN"
						self.sendMessage(chat_id=chat_id
							,text="Bot messages will be shown in English."
							)
					elif message in list(LANGUAGE_INDICIES.keys()):
						#message is a language pick
						self.subscribers[chat_id][1] = LANGUAGE_INDICIES[message]
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,LANGUAGE_IS_SET_TO_MESSAGE) + message
							)
					else:
						if message[0] == "/":
							message = message[1:]
						message = message.replace("_","").replace("*","").replace("`","")

						page_url = 'http://www.multitran.ru/c/m.exe?l1='+str(self.subscribers[chat_id][1]) +'&s=' + message
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
							page_url = 'http://www.multitran.ru/c/m.exe?l1=2&l2='+ str(self.subscribers[chat_id][1]) + '&s=' + message
							page = getHTML_specifyEncoding(page_url, encoding='cp1251',method='replace')
							soup = BeautifulSoup(page)

							temp1 = [i for i in soup.find_all('table') if not i.has_attr('class') and not i.has_attr('id') and not i.has_attr('width') and i.has_attr('cellpadding') and i.has_attr('cellspacing') and i.has_attr('border') and not len(i.find_all('table'))]

							# Maybe there is no such word?
							if not len(temp1):
								result=self.languageSupport(chat_id,WORD_NOT_FOUND_MESSAGE)
								varia = soup.find_all('td',string=re.compile("Варианты"))
								print("varia",varia)
								if varia:
									logging.warning("Есть варианты замены!")
									# print(varia[0].find_next_sibling("td").find_all('a'))
									# quit()
									result += "\n" + self.languageSupport(chat_id,POSSIBLE_REPLACEMENTS_MESSAGE) + varia[0].find_next_sibling("td").text.replace("_","").replace("*","").replace("`","")

							else:
								#request is in Russian
								temp1= temp1[0]
								result = process_result(temp1)

						else:
							#request is in foreign language
							temp1= temp1[0]
							result = process_result(temp1)

						result += self.languageSupport(chat_id,LINK_TO_DICT_PAGE_MESSAGE) + page_url.replace(" ","+")

						result += self.languageSupport(chat_id,CURRENT_LANGUAGE_IS_MESSAGE) + list(LANGUAGE_INDICIES.keys())[list(LANGUAGE_INDICIES.values()).index(self.subscribers[chat_id][1]) ]

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