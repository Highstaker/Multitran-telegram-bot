#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from textual_data import *


def getMainMenu():
	"""
	Returns a representation of custom keyboard to be passed to message-sending functions
	:return: list of lists
	"""

	MAIN_MENU_KEY_MARKUP = [
		[PICK_LANGUAGE_BUTTON],
		[HELP_BUTTON,ABOUT_BUTTON,RATE_ME_BUTTON,OTHER_BOTS_BUTTON],
		[TOGGLE_TRANSLATIONS_LINKS_BUTTON, TOGGLE_TRANSCRIPTIONS_BUTTON],
		[EN_LANG_BUTTON,RU_LANG_BUTTON],
		list(LANGUAGE_INDICIES.keys())
							]

	return MAIN_MENU_KEY_MARKUP
