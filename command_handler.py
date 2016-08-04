import functools
from threading import Thread
from queue import Queue
from os import remove as removeFile

from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ParseMode

from textual_data import *
from language_support import LanguageSupport
from userparams import UserParams
from button_handler import getMainMenu
from multitran_processor import dictQuery
from activity_logger import ActivityLogger

def is_integer(s):
	"""
	If a string is an integer, returns True
	"""
	try:
		int(s)
		return True
	except ValueError:
		return False

def split_list(alist,max_size=1):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(alist), max_size):
		yield alist[i:i+max_size]

async_command_runner_thread = None
async_command_queue = Queue()

def async_command_runner():
	"""Thread that runs processors one after another"""
	while True:
		func, self, bot, update = async_command_queue.get()
		# print("running processor")#debug
		func(self, bot, update)

def command_async(func):
	"""runs a command processor in a separate thread. Uses a queue to run processors one after another"""
	@functools.wraps(func)
	def async_wrapper(self, bot, update):
		# print("async")#debug
		global async_command_runner_thread
		if not async_command_runner_thread or not async_command_runner_thread.is_alive():
			async_command_runner_thread = t = Thread(target=async_command_runner)
			t.start()
		# print("putting")#debug
		async_command_queue.put((func, self, bot, update,))
	return async_wrapper


class UserCommandHandler(object):
	"""docstring for UserCommandHandler"""
	def __init__(self, dispatcher):
		super(UserCommandHandler, self).__init__()
		self.dispatcher = dispatcher

		self.userparams = UserParams(USERS_DB_FILENAME)

		self.activity_logger = ActivityLogger()

		self._addHandlers()

	def _addHandlers(self):
		self.dispatcher.add_handler(CommandHandler('start', self.command_start))
		self.dispatcher.add_handler(CommandHandler('help', self.command_help))
		self.dispatcher.add_handler(CommandHandler('about', self.command_about))
		self.dispatcher.add_handler(CommandHandler('rate', self.command_rateme))
		self.dispatcher.add_handler(CommandHandler('otherbots', self.command_otherbots))
		self.dispatcher.add_handler(CommandHandler('links', self.command_toggle_links))
		self.dispatcher.add_handler(CommandHandler('transcriptions', self.command_toggle_transcriptions))
		self.dispatcher.add_handler(CommandHandler('bottom_row', self.command_toggle_bottom_row))
		self.dispatcher.add_handler(CommandHandler('estadisticas', self.command_send_activity_graph))


		# non-command message
		self.dispatcher.add_handler(MessageHandler([Filters.text], self.messageMethod))

		# unknown commands
		self.dispatcher.add_handler(MessageHandler([Filters.command], self.unknown_command))


		self.dispatcher.add_error_handler(self.error_handler)

	def sendFile(self, bot, update, filename, caption=None):
		chat_id = update.message.chat_id
		with open(filename, "rb") as f:
			bot.sendDocument(chat_id, document=f, caption=caption)

	def sendPic(self, bot, update, pic_filename, caption=""):
		chat_id = update.message.chat_id
		with open(pic_filename,"rb") as pic:
			bot.sendPhoto(chat_id, pic, caption)

	def sendMessage(self, bot, update, message, key_markdown=None, disable_web_page_preview=True):
		def breakLongMessage(msg, max_chars_per_message=2048):
			"""
			Breaks a message that is too long.
			:param max_chars_per_message: maximum amount of characters per message.
			The official maximum is 4096.
			Changing this is not recommended.
			:param msg: message to be split
			:return: a list of message pieces
			"""

			# let's split the message by newlines first
			message_split = msg.split("\n")

			# the result will be stored here
			broken = []

			# splitting routine
			while message_split:
				result = message_split.pop(0) + "\n"
				if len(result) > max_chars_per_message:
					# The chunk is huge. Split it not caring for newlines.
					broken += [result[i:i + max_chars_per_message].strip("\n\t\r ")
							   for i in range(0, len(result), max_chars_per_message)]
				else:
					# It's a smaller chunk, append others until their sum is bigger than maximum
					while len(result) <= max_chars_per_message:
						if not message_split:
							# if the original ran out
							break
						# check if the next chunk makes the merged chunk it too big
						if len(result) + len(message_split[0]) <= max_chars_per_message:
							# nope. append chunk
							result += message_split.pop(0) + "\n"
						else:
							# yes, it does. Stop on this.
							break
					broken += [result.strip("\n\t\r ")]

			return broken


		chat_id = update.message.chat_id
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport
		msg = lS(message)
		if not key_markdown:
			key_markdown = MMKM = lS(getMainMenu(hide_keys=self.userparams.getEntry(chat_id, "buttons_hidden"),
												hide_bottom_row=self.userparams.getEntry(chat_id, "bottom_lang_row_hidden")
												))

		for m in breakLongMessage(msg):
			bot.sendMessage(chat_id=chat_id, text=m,
						reply_markup=ReplyKeyboardMarkup(key_markdown, resize_keyboard=True),
						parse_mode=ParseMode.MARKDOWN,
						disable_web_page_preview=disable_web_page_preview,
						)

	##########
	# COMMAND METHODS
	##########

	def _command_method(func):
		"""Decorator for functions that are invoked on commands. Ensures that the user is initialized."""
		@functools.wraps(func)
		def wrapper(self, bot, update,  *args, **kwargs):
			# print("command method", func.__name__,)#debug
			# print("command method", self, bot, update,  args, kwargs, sep="||")#debug
			chat_id = update.message.chat_id

			# Initialize user, if not present in DB
			self.userparams.initializeUser(chat_id=chat_id)

			# filter functions that don't need ticks, or else there will be two ticks on every non-slash command
			# because it also counts messageMethod
			if func.__name__ not in ("messageMethod"):
				# write a tick to user activity log
				self.activity_logger.tick(chat_id)

			# noinspection PyCallingNonCallable
			func(self, bot, update, *args, **kwargs)
		return wrapper

	# noinspection PyArgumentList
	@_command_method
	def command_start(self, bot, update):
		self.sendMessage(bot, update, START_MESSAGE)
	
	# noinspection PyArgumentList
	@_command_method
	def command_help(self, bot, update):
		msg = HELP_MESSAGE
		self.sendMessage(bot, update, msg)

	# noinspection PyArgumentList
	@_command_method
	@command_async
	def command_send_activity_graph(self, bot, update):
		filename = self.activity_logger.visualizeTicks()
		self.sendFile(bot, update, filename, caption="Bot statistics")
		removeFile(filename)
	
	# noinspection PyArgumentList
	@_command_method
	def command_about(self, bot, update):
		chat_id = update.message.chat_id
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport
		msg = lS(ABOUT_MESSAGE).format(".".join([str(i) for i in VERSION_NUMBER]))
		self.sendMessage(bot, update, msg, disable_web_page_preview=False)
	
	# noinspection PyArgumentList
	@_command_method
	def command_rateme(self, bot, update):
		self.sendMessage(bot, update, RATE_ME_MESSAGE)
	
	# noinspection PyArgumentList
	@_command_method
	def command_otherbots(self, bot, update):
		self.sendMessage(bot, update, OTHER_BOTS_MESSAGE)
	
	# noinspection PyArgumentList
	@_command_method
	def command_toggle_links(self, bot, update):
		chat_id = update.message.chat_id
		links_on = self.userparams.getEntry(chat_id, param="word_links")
		self.userparams.setEntry(chat_id, param="word_links", value=int(not links_on))
		if links_on:
			msg = TRANSLATION_LINKS_OFF_MESSAGE
		else:
			msg = TRANSLATION_LINKS_ON_MESSAGE
		self.sendMessage(bot, update, msg)

	# noinspection PyArgumentList
	@_command_method
	def command_toggle_transcriptions(self, bot, update):
		chat_id = update.message.chat_id
		t_on = self.userparams.getEntry(chat_id, param="transcriptions_on")
		self.userparams.setEntry(chat_id, param="transcriptions_on", value=int(not t_on))
		if t_on:
			msg = TRANSCRIPTIONS_OFF_MESSAGE
		else:
			msg = TRANSCRIPTIONS_ON_MESSAGE
		self.sendMessage(bot, update, msg)

	# noinspection PyArgumentList
	@_command_method
	def command_hide_keyboard(self, bot, update):
		chat_id = update.message.chat_id
		self.userparams.setEntry(chat_id, "buttons_hidden", 1)
		self.sendMessage(bot, update, KEYBOARD_HIDDEN_MESSAGE)

	# noinspection PyArgumentList
	@_command_method
	def command_show_keyboard(self, bot, update):
		chat_id = update.message.chat_id
		self.userparams.setEntry(chat_id, "buttons_hidden", 0)
		self.sendMessage(bot, update, KEYBOARD_SHOWN_MESSAGE)

	# noinspection PyArgumentList
	@_command_method
	def	command_toggle_bottom_row(self, bot, update):
		chat_id = update.message.chat_id
		hidden = self.userparams.getEntry(chat_id, "bottom_lang_row_hidden")
		self.userparams.setEntry(chat_id, "bottom_lang_row_hidden", int(not hidden))
		self.sendMessage(bot, update, "bottom row")

	# noinspection PyArgumentList
	@_command_method
	def command_set_lang_en(self, bot, update):
		chat_id = update.message.chat_id
		self.userparams.setEntry(chat_id, param="lang", value="EN")
		self.sendMessage(bot, update, EN_LANG_MESSAGE)

	# noinspection PyArgumentList
	@_command_method
	def command_set_lang_ru(self, bot, update):
		chat_id = update.message.chat_id
		self.userparams.setEntry(chat_id, param="lang", value="RU")
		self.sendMessage(bot, update, RU_LANG_MESSAGE)
	
	# noinspection PyArgumentList
	@_command_method
	def command_open_language_menu(self, bot, update):
		chat_id = update.message.chat_id
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport
		LANGUAGE_PICK_KEY_MARKUP = list(split_list(list(LANGUAGE_INDICIES.keys()), 3)) + [[lS(BACK_BUTTON)]]
		self.sendMessage(bot, update, SELECT_DICT_LANGUAGE_MESSAGE, key_markdown=LANGUAGE_PICK_KEY_MARKUP)
	
	# noinspection PyArgumentList
	@_command_method
	def command_set_dict_language(self, bot, update):
		chat_id = update.message.chat_id
		message = update.message.text
		self.userparams.setEntry(chat_id, param="dict_lang", value=LANGUAGE_INDICIES[message])
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport
		self.sendMessage(bot, update, lS(LANGUAGE_IS_SET_TO_MESSAGE) + message)

	# noinspection PyArgumentList
	@_command_method
	@command_async
	def command_find_word(self, bot, update):
		self.findWord(bot, update)

	def findWord(self, bot, update, word=None):
		"""A method to find a word in dictionary. If word is provided, it is used.
		If not, it is taken from the update."""
		if word:
			msg = word
		else:
			msg = update.message.text
		chat_id = update.message.chat_id
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport

		lang = self.userparams.getEntry(chat_id, "dict_lang")
		links_on = bool(self.userparams.getEntry(chat_id, 'word_links'))

		result = dictQuery(msg, lang, links_on)

		if result == 1:
			self.sendMessage(bot, update, MULTITRAN_DOWN_MESSAGE)
		else:
			reply = ''
			if isinstance(result, tuple):
				page_url = result[2]
				cur_lang = [i for i in LANGUAGE_INDICIES.keys() if LANGUAGE_INDICIES[i] == lang][0]
				db_variants = ""
				transcription_filename = ""
				if result[0] == 0:
					#word found, print result
					reply += result[1]
					db_variants = ";".join(map(lambda x: x.replace(";", "").strip(" \n\t\r"),result[3]))
					transcription_filename = result[4]

				elif result[0] == 2:
					# Word not found. Replacements may be present
					variants = result[1]
					string_variants = ""
					for n, variant in enumerate(variants):
						string_variants += "/" + str(n) + " " + variant + "\n"
					db_variants = ";".join(map(lambda x: x.replace(";", "").strip(" \n\t\r"), variants))
					self.userparams.setEntry(chat_id, "variants", db_variants)
					reply = "{0}\n{1}\n{2}".format(lS(WORD_NOT_FOUND_MESSAGE),
											lS(POSSIBLE_REPLACEMENTS_MESSAGE) if variants else "",
												 string_variants)

				reply += "{0}: {1}\n{2} {3}.".format(lS(LINK_TO_DICT_PAGE_MESSAGE), page_url,
													 lS(CURRENT_LANGUAGE_IS_MESSAGE), cur_lang)

				self.sendMessage(bot, update, reply)
				self.userparams.setEntry(chat_id, "variants", db_variants)
				if self.userparams.getEntry(chat_id, "transcriptions_on"):
					if transcription_filename:
						self.sendPic(bot, update, transcription_filename, caption=msg)
						removeFile(transcription_filename)


	# noinspection PyArgumentList
	@_command_method
	def unknown_command(self, bot, update):
		msg = update.message.text
		chat_id = update.message.chat_id
		if is_integer(msg[1:]):
			# get the latest word list from DB and get the word from it by index
			try:
				word = self.userparams.getEntry(chat_id, "variants").split(";")[int(msg[1:])]
				self.findWord(bot, update, word=word)
			except IndexError:
				self.sendMessage(bot, update, UNKNOWN_COMMAND_MESSAGE)
		else:
			self.sendMessage(bot, update, UNKNOWN_COMMAND_MESSAGE)
	
	# noinspection PyArgumentList
	@_command_method
	def messageMethod(self, bot, update):
		chat_id = update.message.chat_id
		message = update.message.text

		if message in LanguageSupport.allVariants(HELP_BUTTON):
			self.command_help(bot, update)
		elif message in LanguageSupport.allVariants(ABOUT_BUTTON):
			self.command_about(bot, update)
		elif message in LanguageSupport.allVariants(OTHER_BOTS_BUTTON):
			self.command_otherbots(bot, update)
		elif message in LanguageSupport.allVariants(RATE_ME_BUTTON):
			self.command_rateme(bot, update)
		elif message in LanguageSupport.allVariants(TOGGLE_TRANSLATIONS_LINKS_BUTTON):
			self.command_toggle_links(bot, update)
		elif message in LanguageSupport.allVariants(TOGGLE_TRANSCRIPTIONS_BUTTON):
			self.command_toggle_transcriptions(bot, update)
		elif message == EN_LANG_BUTTON:
			self.command_set_lang_en(bot, update)
		elif message == RU_LANG_BUTTON:
			self.command_set_lang_ru(bot, update)
		elif message in LanguageSupport.allVariants(PICK_LANGUAGE_BUTTON):
			self.command_open_language_menu(bot, update)
		elif message in LanguageSupport.allVariants(HIDE_KEYS_BUTTON):
			self.command_hide_keyboard(bot, update)
		elif message in LanguageSupport.allVariants(SHOW_KEYS_BUTTON):
			self.command_show_keyboard(bot, update)
		elif message in LanguageSupport.allVariants(BACK_BUTTON):
			self.sendMessage(bot, update, BACK_TO_MAIN_MENU_MESSAGE)
		elif message in LANGUAGE_INDICIES.keys():
			self.command_set_dict_language(bot, update)
		else:
			# find word in dict
			pass
			# self.unknown_command(bot, update)
			self.command_find_word(bot, update)

	def error_handler(self, bot, update, error):
		print("[ERROR]", error)