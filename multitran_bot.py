#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#TODO
#-make donation info

VERSION_NUMBER = (0, 8, 4)

import logging
import telegram
from time import time, sleep
from os import path, listdir, walk, makedirs
import socket
import pickle #module for saving dictionaries to file
from bs4 import BeautifulSoup #HTML parser
import re
import requests
import io
from PIL import Image
import itertools

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

#A name and path for a temporary transcription file
TRANSCRIPTION_TEMP_IMAGE_FILENAME = '/tmp/transcript.png'

#A path to store cached transcription letter images
TRANSCRIPTION_LETTER_CACHE_PATH = '/tmp/transcription_letters_cache/'

#A path where subscribers list is saved.
SUBSCRIBERS_BACKUP_FILE = 'multitran_bot_subscribers_bak.save'

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
, "🇪🇪 Estonian":26
, "🇿🇦 Afrikaans":31
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
EN_LANG_BUTTON = "Bot language:🇬🇧 EN"
RU_LANG_BUTTON = "Язык бота:🇷🇺 RU"
OTHER_BOTS_BUTTON = {"EN":"👾 My other bots", "RU": "👾 Другие мои боты"}

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

OTHER_BOTS_MESSAGE = {"EN": """*My other bots*:

@OmniCurrencyExchangeBot: a currency converter bot supporting past rates and graphs.
"""
, "RU": """*Другие мои боты*:
@OmniCurrencyExchangeBot: Конвертер валют с поддержкой графиков и прошлых курсов.
"""
}

LANGUAGE_IS_SET_TO_MESSAGE = {"EN": "Language is set to ", "RU":"Язык установлен на "}

SELECT_DICT_LANGUAGE_MESSAGE = {"EN": "Select language", "RU":"Выберите язык"}

BACK_TO_MAIN_MENU_MESSAGE = {"EN": "Back to Main Menu", "RU":"Вы вернулись в главное меню"}

WORD_NOT_FOUND_MESSAGE = {"EN": "*Word not found!*", "RU": "*Слово не найдено!*"}

POSSIBLE_REPLACEMENTS_MESSAGE = {"EN": "*Possible replacements: *", "RU": "*Варианты замены: *"}

LINK_TO_DICT_PAGE_MESSAGE = {"EN": "\nLink to the dictionary page: ", "RU": "\nСсылка на страницу словаря: " }

CURRENT_LANGUAGE_IS_MESSAGE = {"EN": "\nCurrent language is ", "RU": "\nВыбранный язык:" }

OPTION_TOGGLE_TRANSLATIONS_LINKS = {"EN": "Toggle translation links", "RU": "Вкл/выкл ссылки"}

TRANSLATION_LINKS_ON_MESSAGE = {"EN": "Links in translations are now enabled", "RU": "Ссылки в переводах включены"}

TRANSLATION_LINKS_OFF_MESSAGE = {"EN": "Links in translations are now disabled", "RU": "Ссылки в переводах выключены"}

def split_list(alist,max_size=1):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(alist), max_size):
		yield alist[i:i+max_size]

MAIN_MENU_KEY_MARKUP = [[PICK_LANGUAGE_BUTTON],
[HELP_BUTTON,ABOUT_BUTTON,RATE_ME_BUTTON,OTHER_BOTS_BUTTON],
[EN_LANG_BUTTON,RU_LANG_BUTTON],
[OPTION_TOGGLE_TRANSLATIONS_LINKS],
list(LANGUAGE_INDICIES.keys())]

LANGUAGE_PICK_KEY_MARKUP = list(  split_list( list(LANGUAGE_INDICIES.keys()) ,3)  ) + [[BACK_BUTTON]]

#This is assigned to user when it is created
DEFAULT_SUBSCRIBERS = ["EN",1,[],True]

################
###GLOBALS######
################

with open(path.join(path.dirname(path.realpath(__file__)), TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

#############
##METHODS###
############

def is_integer(s):
	'''
	If a string is an integer, returns True
	'''
	try:
		int(s)
		return True
	except ValueError:
		return False


###############
###CLASSES#####
###############

class TelegramBot():
	"""The bot class"""

	LAST_UPDATE_ID = None

	#{chat_id: [Language_of_bot,LANGUAGE_INDEX_of_dictionary,list_of_possible_replacements] ...}
	subscribers = {}

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		#get data for all users
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
				logging.warning(("self.subscribers",self.subscribers))
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
						reply_markup=telegram.ReplyKeyboardMarkup(key_markup, resize_keyboard=True)
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

	def sendPic(self,chat_id,pic,caption=None):
		logging.warning("Sending image to " + str(chat_id) + " " + str(pic))
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				self.bot.sendChatAction(chat_id,telegram.ChatAction.UPLOAD_PHOTO)
				#set file read cursor to the beginning. This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id,photo=pic,caption=caption)
			except Exception as e:
				if ("urlopen error" in str(e)) or ("timed out" in str(e)):
					logging.error("Could not send message. Retrying! Error: " + str(e))
					sleep(3)
					continue
				else:
					logging.error("Could not send message. Error: " + str(e))
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
				self.subscribers[chat_id] = DEFAULT_SUBSCRIBERS
				self.saveSubscribers()

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
					elif message == "/otherbots" or message == self.languageSupport(chat_id,OTHER_BOTS_BUTTON):
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,OTHER_BOTS_MESSAGE)
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
					elif message == self.languageSupport(chat_id,OPTION_TOGGLE_TRANSLATIONS_LINKS):
						self.subscribers[chat_id][3] = not self.subscribers[chat_id][3]
						if self.subscribers[chat_id][3]:
							self.sendMessage(chat_id=chat_id
								,text=self.languageSupport(chat_id,TRANSLATION_LINKS_ON_MESSAGE)
								)
						else:
							self.sendMessage(chat_id=chat_id
								,text=self.languageSupport(chat_id,TRANSLATION_LINKS_OFF_MESSAGE)
								)
					elif message == RU_LANG_BUTTON:
						self.subscribers[chat_id][0] = "RU"
						self.saveSubscribers()
						self.sendMessage(chat_id=chat_id
							,text="Сообщения бота будут отображаться на русском языке."
							)
					elif message == EN_LANG_BUTTON:
						self.subscribers[chat_id][0] = "EN"
						self.saveSubscribers()
						self.sendMessage(chat_id=chat_id
							,text="Bot messages will be shown in English."
							)
					elif message in list(LANGUAGE_INDICIES.keys()):
						#message is a language pick
						self.subscribers[chat_id][1] = LANGUAGE_INDICIES[message]
						self.saveSubscribers()
						self.sendMessage(chat_id=chat_id
							,text=self.languageSupport(chat_id,LANGUAGE_IS_SET_TO_MESSAGE) + message
							)
					else:
						if message[0] == "/":
							message = message[1:]
							if is_integer(message):
								try:
									message = self.subscribers[chat_id][2][int(message)]
								except IndexError:
									logging.warning("No such index in variants_list!")

						message = message.replace("_","").replace("*","").replace("`","")

						page_url = 'http://www.multitran.ru/c/m.exe?l1='+str(self.subscribers[chat_id][1]) +'&s=' + message
						page = getHTML_specifyEncoding(page_url, encoding='cp1251',method='replace')
						soup = BeautifulSoup(page,"lxml")

						temp1 = [i for i in soup.find_all('table') if not i.has_attr('class') and not i.has_attr('id') and not i.has_attr('width') and i.has_attr('cellpadding') and i.has_attr('cellspacing') and i.has_attr('border') 
						and not len(i.find_all('table'))
						]

						def process_result(temp1,chat_id):
							result = ""
							transcription_images_links = []
							word_index = 0
							self.subscribers[chat_id][2] = []
							for tr in temp1.find_all('tr'):
								tds = tr.find_all('td')
								def translations_row(chat_id,word_index):
									result = "`" + tr.find_all('a')[0].text + "`" + " "*5
									for a in tr.find_all('a')[1:]:
										if not 'i' in [i.name for i in a.children]:
											i_word = a.text.replace("_","").replace("*","").replace("`","")
											a_word = i_word + "; "
											self.subscribers[chat_id][2] += [i_word]
											result += (a_word) if not self.subscribers[chat_id][3] else ("/" + str(word_index) + " " + a_word + "\n")
											word_index += 1
									return (result,word_index)

								if tds[0].has_attr('bgcolor'):
									if tds[0]['bgcolor'] == "#DBDBDB":
										#an initial word
										result += "\n" + "*" + tr.text.split("|")[0].replace(tr.find_all('em')[0].text if tr.find_all('em') else "","").replace("в начало","").replace("фразы","").replace("\n","").replace("_","").replace("*","") + "*" + ( ( " "*5 + "_" + tr.find_all('em')[0].text  + "_") if tr.find_all('em') else "" )
										transcription_images_links += [ [i["src"] for i in tr.find_all('img')] ]
									else:
										#translations
										r, word_index = translations_row(chat_id,word_index)
										result += r
								else:
									r, word_index = translations_row(chat_id,word_index)
									result += r
								result += "\n"

							# print(transcription_images_links)#debug
							self.saveSubscribers()
							return result, transcription_images_links



						result=""
						transcription_images_links = []
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
								if varia:
									variants_list = [i for i in varia[0].find_next_sibling("td").text.replace("_","").replace("*","").replace("`","").split(";")]
									self.subscribers[chat_id][2] = variants_list
									self.saveSubscribers()
									result += "\n" + self.languageSupport(chat_id,POSSIBLE_REPLACEMENTS_MESSAGE) + "\n".join([("/"+str(n) + " " + i) for n,i in enumerate(variants_list) ])

							else:
								#request is in Russian
								temp1= temp1[0]
								result, transcription_images_links = process_result(temp1,chat_id)

						else:
							#request is in foreign language
							temp1= temp1[0]
							result, transcription_images_links = process_result(temp1,chat_id)

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
						
						#######
						#create transcriptions and send
						########

						# downloading letters
						def removeListDuplicates(k):
							'''
							Removes duplicates from a list `k`. Usable with a list of lists.
							WARNING! Screws the order up!
							'''
							k.sort()
							return [i for i,j in itertools.groupby(k)]

						def getLetterOnline(letter_page):
							'''gets a letter picture from multitran'''
							# print("letter_page",letter_page)
							while True:
								try:
									req=requests.get("http://www.multitran.ru" + letter_page)
									if req.ok:
										c = req.content
										image_file = io.BytesIO(c)
										with open(path.join(TRANSCRIPTION_LETTER_CACHE_PATH,path.basename(letter_page)),'wb') as f:
											f.write(c)
										# image = Image.open(image_file)
										# letter_images += [image]
										break
								except Exception as e:
									logging.error("Could not get transcription letter image. Error: " + str(e))
									pass
							return image_file


						transcription_images_links = [i for i in removeListDuplicates(transcription_images_links) if i]#remove duplicate lists of files, thus removing duplicate images. Also, remove emties if they appear
						# print(transcription_images_links)#debug
						if transcription_images_links:
							for transcription in transcription_images_links:
								letter_images = []
								for letter_page in transcription:
									#try opening a cached file
									try:
										makedirs(TRANSCRIPTION_LETTER_CACHE_PATH,exist_ok=True)#make a directory. Ignore if it already exists
										with open(path.join(TRANSCRIPTION_LETTER_CACHE_PATH,path.basename(letter_page)),'rb') as f:
											image_file = io.BytesIO(f.read())
									except FileNotFoundError:
										#if failed, download it
										image_file = getLetterOnline(letter_page)
									
									try:
										#in case the cache is damaged
										image = Image.open(image_file)
									except:
										image = Image.open(getLetterOnline(letter_page))

									letter_images += [image]

								#creating a whole image
								image_sizes = [i.size for i in letter_images]
								max_height = max([i[1] for i in image_sizes])
								whole_transcription_image = Image.new('RGB',( sum([i[0] for i in image_sizes]) , max_height  ) )
								horiz_offset = 0
								for i in letter_images:
									whole_transcription_image.paste( i,(horiz_offset,0) )
									horiz_offset += i.size[0]

								whole_transcription_image = whole_transcription_image.convert('L')
								whole_transcription_image = whole_transcription_image.point(lambda x: 0 if x<128 else 255, '1')

								whole_transcription_image.save(TRANSCRIPTION_TEMP_IMAGE_FILENAME)

								#send image
								with open(TRANSCRIPTION_TEMP_IMAGE_FILENAME,'rb') as pic:
									self.sendPic(chat_id=chat_id
										,pic=pic
										)

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