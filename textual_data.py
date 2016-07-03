from os import path
import sys

VERSION_NUMBER = (1, 0, 1)

if getattr(sys, 'frozen', False):
	# frozen
	SCRIPT_FOLDER = path.dirname(sys.executable)
else:
	SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

#################
##### FILENAMES##
#################

DATABASES_FOLDER_NAME = "databases"
USERS_DB_FILENAME = "users"

# A filename of a file containing Telegram bot token.
BOT_TOKEN_FILENAME = 'tokens/token'
with open(path.join(SCRIPT_FOLDER, BOT_TOKEN_FILENAME), 'r') as f:
	BOT_TOKEN = f.read().replace("\n", "")

# Indicies that correspond to various languages on Multitran
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

#################
#### BUTTONS#####
#################

HELP_BUTTON = {"EN" : "⁉️" + "Help", "RU": "⁉️" + "Помощь"}
PICK_LANGUAGE_BUTTON = {"EN" : "🇬🇧🇫🇷🇮🇹🇩🇪🇳🇱🇪🇸 Pick Dictionary Language", "RU": "🇬🇧🇫🇷🇮🇹🇩🇪🇳🇱🇪🇸 Выбор языка словаря"}
BACK_BUTTON = {"EN" : "⬅️ Back", "RU": "⬅️ Назад"}
ABOUT_BUTTON = {"EN" : "ℹ️ About", "RU": "ℹ️ О программе"}
RATE_ME_BUTTON = {"EN" : "⭐️ Like me? Rate!", "RU": "⭐️ Нравится бот? Оцени!"}
EN_LANG_BUTTON = "Bot language:🇬🇧 EN"
RU_LANG_BUTTON = "Язык бота:🇷🇺 RU"
OTHER_BOTS_BUTTON = {"EN":"👾 My other bots", "RU": "👾 Другие мои боты"}
TOGGLE_TRANSLATIONS_LINKS_BUTTON = {"EN": "Toggle translation links", "RU": "Вкл/выкл ссылки"}


##############
#### TEXTS####
##############

EN_LANG_MESSAGE = "Interface language is set ot English"

RU_LANG_MESSAGE = "Язык интерфейса русский"

LANGUAGE_IS_SET_TO_MESSAGE = {"EN": "Language is set to ", "RU":"Язык установлен на "}

SELECT_DICT_LANGUAGE_MESSAGE = {"EN": "Select dictionary language", "RU": "Выберите язык словаря"}

BACK_TO_MAIN_MENU_MESSAGE = {"EN": "Back to Main Menu", "RU":"Вы вернулись в главное меню"}

WORD_NOT_FOUND_MESSAGE = {"EN": "*Word not found!*", "RU": "*Слово не найдено!*"}

POSSIBLE_REPLACEMENTS_MESSAGE = {"EN": "*Possible replacements: *", "RU": "*Варианты замены: *"}

LINK_TO_DICT_PAGE_MESSAGE = {"EN": "\nLink to the dictionary page: ", "RU": "\nСсылка на страницу словаря: " }

CURRENT_LANGUAGE_IS_MESSAGE = {"EN": "\nCurrent language is ", "RU": "\nВыбранный язык:" }

TRANSLATION_LINKS_ON_MESSAGE = {"EN": "Links in translations are now enabled", "RU": "Ссылки в переводах включены"}

TRANSLATION_LINKS_OFF_MESSAGE = {"EN": "Links in translations are now disabled", "RU": "Ссылки в переводах выключены"}

UNKNOWN_COMMAND_MESSAGE = {"EN": "Unknown command", "RU": "Неизвестная команда"}

##################
#### BIG TEXTS####
##################


HELP_MESSAGE = {"EN": '''
This bot connects to Multitran dictionary to translate between Russian and a selected language.
By default it is set to English.
To translate a word, type it.
To change language click the `{0}` button.

Available languages are: {1}'''.format(PICK_LANGUAGE_BUTTON["EN"], ", ".join(list(LANGUAGE_INDICIES.keys()))),
"RU": '''
Этот бот может переводить слова и выражения с русского языка на иностранный и наоборот.

Чтобы перевести слово, просто введите его. Русское слово будет переведено на выбранный иностранный язык, а иностранное - на русский.

По умолчанию в качестве иностранного выставлен английский язык.
Чтобы изменить язык, нажмите кнопку `{0}` и выберите язык в меню.

Доступные языки: {1}
'''.format(PICK_LANGUAGE_BUTTON["RU"], ", ".join(list(LANGUAGE_INDICIES.keys()))),
}

ABOUT_MESSAGE = {"EN": """*Multitran Bot*
_Created by:_ Highstaker a.k.a. OmniSable.
Get in touch with me on Telegram if you have questions, suggestions or bug reports (@Highstaker).
Source code can be found [here](https://github.com/Highstaker/Multitran-telegram-bot).
Version: {0}
[My channel, where I post development notes and update news](https://telegram.me/highstakerdev).

This bot uses the [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot) library.

Translation data is received from [Multitran online dictionary](multitran.ru).
""",
"RU": """*Multitran Bot*
_Автор:_ Highstaker a.k.a. OmniSable.
По вопросам и предложениям обращайтесь в Телеграм (@Highstaker).
Исходный код [здесь](https://github.com/Highstaker/Multitran-telegram-bot).
Версия: {0}
[Мой канал, где я объявляю о новых версиях ботов](https://telegram.me/highstakerdev).

Этот бот написан на основе библиотеки [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

Переводы берутся из [словаря Мультитран](multitran.ru).
"""
}


START_MESSAGE = "Welcome! Type /help to get help."

RATE_ME_MESSAGE = {"EN": """
You seem to like this bot. You can rate it [here](https://storebot.me/bot/multitran_bot)!

Your ⭐️⭐️⭐️⭐️⭐️ would be really appreciated!
""",
"RU": """
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