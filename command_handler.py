import functools
from threading import Thread, Lock
from queue import Queue

from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ParseMode

from textual_data import *
from language_support import LanguageSupport
from userparams import UserParams
from button_handler import getMainMenu
from multitran_processor import MultitranProcessor


def split_list(alist,max_size=1):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(alist), max_size):
		yield alist[i:i+max_size]

# async_command_lock = Lock()
async_command_runner_thread = None
async_command_queue = Queue()

def async_command_runner():
	"""Thread that runs processors one after another"""
	while True:
		func, self, bot, update = async_command_queue.get()
		print("running processor")#debug
		func(self, bot, update)

def command_async(func):
	"""runs a command processor in a separate thread. Uses a queue to run processors one after another"""
	@functools.wraps(func)
	def async_wrapper(self, bot, update):
		print("async")#debug
		global async_command_runner_thread
		if not async_command_runner_thread or not async_command_runner_thread.is_alive():
			async_command_runner_thread = t = Thread(target=async_command_runner)
			t.start()
		print("putting")#debug
		async_command_queue.put((func, self, bot, update,))
	return async_wrapper


class UserCommandHandler(object):
	"""docstring for UserCommandHandler"""
	def __init__(self, dispatcher):
		super(UserCommandHandler, self).__init__()
		self.dispatcher = dispatcher

		self.userparams = UserParams(USERS_DB_FILENAME)

		self._addHandlers()

	def _addHandlers(self):
		self.dispatcher.add_handler(CommandHandler('start', self.command_start))
		self.dispatcher.add_handler(CommandHandler('help', self.command_help))
		self.dispatcher.add_handler(CommandHandler('about', self.command_about))
		self.dispatcher.add_handler(CommandHandler('rate', self.command_rateme))
		self.dispatcher.add_handler(CommandHandler('otherbots', self.command_otherbots))
		self.dispatcher.add_handler(CommandHandler('links', self.command_toggle_links))


		# non-command message
		self.dispatcher.add_handler(MessageHandler([Filters.text], self.messageMethod))

		# unknown commands
		self.dispatcher.add_handler(MessageHandler([Filters.command], self.unknown_command))


		self.dispatcher.add_error_handler(self.error_handler)

	def sendMessage(self, bot, update, message, key_markdown=None):
		chat_id = update.message.chat_id
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport
		msg = lS(message)
		if not key_markdown:
			key_markdown = MMKM = lS(getMainMenu())

		bot.sendMessage(chat_id=chat_id, text=msg,
						reply_markup=ReplyKeyboardMarkup(key_markdown, resize_keyboard=True),
						parse_mode=ParseMode.MARKDOWN
						)

	##########
	# COMMAND METHODS
	##########

	def _command_method(func):
		"""Decorator for functions that are invoked on commands. Ensures that the user is initialized."""
		@functools.wraps(func)
		def wrapper(self, bot, update,  *args, **kwargs):
			print("command method",)
			# print("command method", self, bot, update,  args, kwargs, sep="||")#debug
			chat_id = update.message.chat_id
			self.userparams.initializeUser(chat_id=chat_id)

			# noinspection PyCallingNonCallable
			func(self, bot, update,  *args, **kwargs)
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
	def command_about(self, bot, update):
		chat_id = update.message.chat_id
		lS = LanguageSupport(self.userparams.getLang(chat_id)).languageSupport
		msg = lS(ABOUT_MESSAGE).format(".".join([str(i) for i in VERSION_NUMBER]))
		self.sendMessage(bot, update, msg)
	
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


		# TESTING CRAP
		for i in range(30000):
			a = 2**i
			# print(a)
		chat_id = update.message.chat_id
		bot.sendMessage(chat_id, "OKAY!")
	
	# noinspection PyArgumentList
	@_command_method
	def unknown_command(self, bot, update):
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
		elif message == EN_LANG_BUTTON:
			self.command_set_lang_en(bot, update)
		elif message == RU_LANG_BUTTON:
			self.command_set_lang_ru(bot, update)
		elif message in LanguageSupport.allVariants(PICK_LANGUAGE_BUTTON):
			self.command_open_language_menu(bot, update)
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