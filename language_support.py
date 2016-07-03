#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from utils import DictUtils as DU

dictI = DU.dictGetCaseInsensitive


class LanguageSupport(object):
	"""A class handling dictionaries of strings in several languages"""

	def __init__(self, lang=None, default_lang="EN"):
		"""
		:param lang: A language that will be extracted from a given message dictionary and returned by languageSupport()
		:param default_lang: If a language given in `lang` is not provided in message dictionary, this language will be used instead
		:return:
		"""
		super(LanguageSupport, self).__init__()
		self.lang = lang
		self.default_lang = default_lang

	def languageSupport(self, message):
		"""
		Returns a message from a dictionary depending on a language chosen by user.
		:param message: the message to process
		If a string is given, it is returned as-is.
		If a dictionary is given, a string with a key set in `self.lang` is given. If it is not in dictionary,
		`self.default_lang` is uesd instead.
		:raises KeyError: if neither `self.lang` nor `self.default_lang` are in the dictionary.
		"""
		lang = self.lang
		if isinstance(message, str):
			result = message
		elif isinstance(message, dict):

			try:
				result = dictI(message, lang)
			except KeyError:
				try:
					result = dictI(message, self.default_lang)
				except KeyError:
					raise KeyError("Message is not available neither in given language ({0}) nor in default one ({1})"
								   .format(self.lang, self.default_lang))

		elif isinstance(message, list):
			# could be a key markup
			result = list(message)
			for n, i in enumerate(message):
				result[n] = self.languageSupport(i)
		else:
			result = ""

		return result

	@staticmethod
	def allVariants(data):
		"""
		Returns a list of all translations, if data is a dictionary.
		If it is a string, returns a list with one entry `data`.
		Returns empty list for all other types.
		:return: a list
		"""
		if isinstance(data, str):
			return [data]
		elif isinstance(data, dict):
			return [i for i in data.values()]
		else:
			return list()
