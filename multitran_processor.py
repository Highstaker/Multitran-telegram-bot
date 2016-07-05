import re
import requests
from bs4 import BeautifulSoup

class MultitranError(Exception):
	pass


def escape_markdown(text):
	"""Helper function to escape telegram markdown symbols"""
	escape_chars = '\*_`\['
	return re.sub(r'([%s])' % escape_chars, r'\\\1', text)

def getTranslationsTable(soup):
	"""Returns the translations table from Multitran page, as an element in the list"""
	table = [i for i in soup.find_all('table') if
			 not i.has_attr('class') and not i.has_attr('id') and not i.has_attr('width') and i.has_attr(
				 'cellpadding') and i.has_attr('cellspacing') and i.has_attr('border')
			 and not len(i.find_all('table'))]
	return table

def getReplacementVariants(soup):
	varia = soup.find_all('td', string=re.compile("Варианты"))
	variants_list = []
	if varia:
		variants_list = [i for i in varia[0].find_next_sibling("td").text.split(";")]
	return variants_list

def processTable(table):
	result = ""
	transcription_images_links = []
	words_list = []
	word_index = 0
	for tr in table.find_all('tr'):
		# for each row, corresponds to topic
		tds = tr.find_all('td')

		def translations_row(word_index):
			result = "`" + tr.find_all('a')[0].text + "`" + " " * 5
			words_list = []
			for a in tr.find_all('a')[1:]:
				if not 'i' in [i.name for i in a.children]:
					i_word = escape_markdown(a.text)
					a_word = i_word + "; "
					words_list += [i_word.strip(" \n\t\r")]
					result += a_word
					# result += (a_word) if not self.subscribers[chat_id][3] else (
					# "/" + str(word_index) + " " + a_word + "\n")
					word_index += 1
			return result, word_index, words_list

		if tds[0].has_attr('bgcolor') and tds[0]['bgcolor'] == "#DBDBDB":
			# a header of the table, with initial word and its properties
			result += "\n" + "*" + escape_markdown(tr.text.split("|")[0].replace(
				tr.find_all('em')[0].text if tr.find_all('em') else "", "").replace("в начало", "").replace("фразы",
																											"").replace(
				"\n", "")) + "*" + (  #cursive
					  (" " * 5 + "_" + escape_markdown(tr.find_all('em')[0].text) + "_") if tr.find_all('em') else "")
			transcription_images_links += [[i["src"] for i in tr.find_all('img')]]
		else:
			r, word_index, word_list_fraction = translations_row(word_index)
			words_list += word_list_fraction
			result += r
		result += "\n"

	return result, transcription_images_links, words_list

def dictQuery(request, lang):
	soup = None
	for russian in range(2):
		# try a foreign language in first iteration, and if not found, try Russian in second one.
		try:
			status_code, page, page_url = getMultitranPage(request, lang, from_russian=bool(russian))
		except MultitranError:
			return 1

		soup = BeautifulSoup(page, "lxml")

		translations_table = getTranslationsTable(soup)
		if translations_table:
			# word is found continue to processing

			# have to extract translations_table[0] from list
			result, transcription_images_links, words_list = processTable(translations_table[0])
			# print(result, transcription_images_links, words_list)#debug

			return 0, result, page_url, words_list
	else:
		# word not found. Process possible variants
		variants = getReplacementVariants(soup)
		if variants:
			return 2, variants, page_url
		else:
			return 2, [], page_url


def getMultitranPage(word, lang, from_russian=False, attempts=3):
	"""Processes the Multitran page. Returns the status code and content."""
	if from_russian:
		page_url = 'http://www.multitran.ru/c/m.exe?l1=2&l2={0}&s={1}'.format(lang, word)
	else:
		page_url = 'http://www.multitran.ru/c/m.exe?l1={0}&s={1}'.format(lang, word)

	for i in range(attempts):
		req = requests.get(page_url)
		if req.status_code == 200:
			break
	else:
		raise MultitranError('Multitran is down!')

	return req.status_code, req.content.decode("cp1251","replace"), page_url

