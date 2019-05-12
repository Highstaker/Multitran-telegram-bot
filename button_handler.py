#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from textual_data import *


def getMainMenu(hide_keys=False, hide_bottom_row=True):
	"""
	Returns a representation of custom keyboard to be passed to message-sending functions
	:return: list of lists
	"""


	if hide_keys:
		MAIN_MENU_KEY_MARKUP = [[SHOW_KEYS_BUTTON]]
	else:
		MAIN_MENU_KEY_MARKUP = [
			[PICK_LANGUAGE_BUTTON],
			[HELP_BUTTON,ABOUT_BUTTON,RATE_ME_BUTTON,OTHER_BOTS_BUTTON],
			[HIDE_KEYS_BUTTON, TOGGLE_TRANSLATIONS_LINKS_BUTTON, #TOGGLE_TRANSCRIPTIONS_BUTTON,
			],
			[EN_LANG_BUTTON,RU_LANG_BUTTON],
			list(LANGUAGE_INDICIES.keys()) if not hide_bottom_row else []
								]

	return MAIN_MENU_KEY_MARKUP
