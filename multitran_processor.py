import re
import requests
import itertools
import io
from os import path, makedirs
from bs4 import BeautifulSoup
from PIL import Image
from random import getrandbits


class MultitranError(Exception):
	pass


def escape_markdown(text):
	"""Helper function to escape telegram markdown symbols"""
	escape_chars = '\*_`\['
	return re.sub(r'([%s])' % escape_chars, r'\\\1', text)


def getTranslationsTable(soup):
	"""Returns the translations table from Multitran page, as an element in the list"""
	# print(soup)#debug
	# div1 = soup.find_all('div', class_='middle_mobile')
	# print("div1", div1)
	tables = soup.find_all('table')
	# print("tables",tables)#debug
	table = [i for i in tables if i.has_attr('width')
and not i.has_attr('class') and not i.has_attr('id')
	][:]

	result = []
	for t in table:
		# print(str(t))
		if "перевод с других языков" not in str(t):
			result.append(t)

	# print(table, result,sep='\n',end='\n==============\n')#debug	

	# table = [i for i in soup.find_all('table') if
	# 		 not i.has_attr('class') and not i.has_attr('id') and not i.has_attr('width') and i.has_attr(
	# 			 'cellpadding') and i.has_attr('cellspacing') and i.has_attr('border')
	# 		 and not len(i.find_all('table'))]
	return result


def getReplacementVariants(soup):
	varia = soup.find_all('td', string=re.compile("Варианты"))
	variants_list = []
	if varia:
		variants_list = [i for i in varia[0].find_next_sibling("td").text.split(";")]
	return variants_list


def processTable(table, links_on=False):
	result = ""
	transcription_images_links = []
	words_list = []
	word_index = 0

	def translations_row(word_index):
		_result = "`" + tr.find_all('a')[0].text + "`" + " " * 5
		_words_list = []
		for a in tr.find_all('a')[1:]:
			if not 'i' in [i.name for i in a.children]:
				i_word = escape_markdown(a.text).strip(" \n\t\r")
				# print(3, i_word)
				if i_word == "в начало":
					break
				a_word = i_word + "; "
				_words_list += [i_word]
				# add a word, checking if a user wants links
				_result += a_word if not links_on else ("/" + str(word_index) + " " + a_word + "\n")
				word_index += 1
		return _result, word_index, _words_list

	for tr in table.find_all('tr'):
		# for each row, corresponds to topic
		tds = tr.find_all('td')
		# print("table",table)#debug
		# print("tr",tr)#debug
		# print("tds", tds)#debug
		# print(tds[0].has_attr('class'), tds[0]['class'] == ['gray'])#debug
		if len(tds) <= 0:
			continue

		if tds[0].has_attr('class') and tds[0]['class'] == ['gray']:
			# print("found header", tr)#debug
			# a header of the table, with initial word and its properties
			# print(1, tr.text)#debug
			result += "\n" + "*" + escape_markdown(tr.text.split("|")[0].replace(
				tr.find_all('em')[0].text if tr.find_all('em') else "", "").replace("в начало", "").replace("фразы",
																											"").replace(
				"\n", "")) + "*" + (  #cursive
					  (" " * 5 + "_" + escape_markdown(tr.find_all('em')[0].text) + "_") if tr.find_all('em') else "")
			# transcription_images_links += [[i["src"] for i in tr.find_all('img')]] #transcriptions are now textual on Multitran
		else:
			# print(2, tr.text)  # debug
			try:
				r, word_index, word_list_fraction = translations_row(word_index)
				words_list += word_list_fraction
				result += r
			except IndexError:
				pass
		result += "\n"

	return result, transcription_images_links, words_list


def dictQuery(request, lang, links_on=False):
	"""

	:param request: a word to search
	:param lang: index of a foreign language
	:param links_on: should the links be present in the reply or not?
	:return: a tuple. First element is always a signal.
	0 - Normal.
	1 - Could not connect to Multitran.
	2 - Word not found.
	"""
	soup = None
	page_url = ""
	for russian in range(2):
		# try a foreign language in first iteration, and if not found, try Russian in second one.
		try:
			status_code, page, page_url = getMultitranPage(request, lang, from_russian=bool(russian))
		except MultitranError:
			return 1

		soup = BeautifulSoup(page, "lxml")

		translations_table = getTranslationsTable(soup)
		# print("translations_table",translations_table)#debug
		if translations_table:
			# word is found continue to processing

			# have to extract translations_table[0] from list
			result, transcription_images_links, words_list = processTable(translations_table[0], links_on)
			# print(result, transcription_images_links, words_list, russian)#debug

			transcription_filename = createTranscription(transcription_images_links)

			return 0, result, page_url, words_list, transcription_filename
	else:
		# word not found. Process possible variants
		variants = getReplacementVariants(soup)
		if variants:
			return 2, variants, page_url
		else:
			return 2, [], page_url


def getMultitranPage(word, lang, from_russian=False, attempts=3):
	"""Processes the Multitran page. Returns the status code and content."""

	# escape the word in URL.
	# try:
	# 	word_escaped = requests.utils.quote(word.encode("cp1251"))
	# except UnicodeEncodeError:
	word_escaped = requests.utils.quote(word.encode('utf-8', 'replace'))

	if from_russian:
		page_url = 'https://www.multitran.com/m.exe?l1=2&l2={0}&s={1}'.format(lang, word_escaped)
	else:
		page_url = 'https://www.multitran.com/m.exe?l1={0}&l2=2&s={1}'.format(lang, word_escaped)

	MULTITRAN_ERROR_TEXT = 'Multitran is down!'

	for i in range(attempts):
		try:
			req = requests.get(page_url)
		except:
			raise MultitranError(MULTITRAN_ERROR_TEXT)
		if req.status_code == 200:
			break
	else:
		raise MultitranError(MULTITRAN_ERROR_TEXT)

	return req.status_code, req.content.decode("utf-8", "replace"), page_url


def createTranscription(transcription_images_links):
	TRANSCRIPTION_LETTER_CACHE_PATH = "/tmp/transcriptions"

	def removeListDuplicates(k):
		'''
		Removes duplicates from a list `k`. Usable with a list of lists.
		WARNING! Screws the order up!
		'''
		k.sort()
		return [i for i, j in itertools.groupby(k)]

	def getLetterOnline(letter_page):
		'''gets a letter picture from multitran'''
		# print("letter_page",letter_page)

		im = None
		while True:
			try:
				req = requests.get("http://www.multitran.com" + letter_page)
				if req.ok:
					c = req.content
					image_file = io.BytesIO(c)
					# Resize the image. They're originally just several pixels in size, that's frustrating.
					RESIZED_HEIGHT = 600
					im = Image.open(image_file)
					im_size = im.size
					im = im.resize((int(RESIZED_HEIGHT * im_size[0]/im_size[1]), RESIZED_HEIGHT), Image.NEAREST)
					im.save(path.join(TRANSCRIPTION_LETTER_CACHE_PATH, path.basename(letter_page)))
					# with open(path.join(TRANSCRIPTION_LETTER_CACHE_PATH, path.basename(letter_page)), 'wb') as f:
					# 	f.write(c)
					break
			except Exception as e:
				# logging.error("Could not get transcription letter image. Error: " + str(e))
				pass
		return im

	transcription_images_links = [i for i in removeListDuplicates(transcription_images_links) if
								  i]  # remove duplicate lists of files, thus removing duplicate images. Also, remove emties if they appear
	# print(transcription_images_links)#debug
	if transcription_images_links:
		for transcription in transcription_images_links:
			letter_images = []
			for letter_page in transcription:
				# try opening a cached file
				try:
					makedirs(TRANSCRIPTION_LETTER_CACHE_PATH,
							 exist_ok=True)  # make a directory. Ignore if it already exists
					image_file = Image.open(path.join(TRANSCRIPTION_LETTER_CACHE_PATH, path.basename(letter_page)))
				except FileNotFoundError:
					# if failed, download it
					image_file = getLetterOnline(letter_page)
					if not image_file:
						return ""

				letter_images += [image_file]

			# creating a whole image
			image_sizes = [i.size for i in letter_images]
			max_height = max([i[1] for i in image_sizes])
			whole_transcription_image = Image.new('RGB', (sum([i[0] for i in image_sizes]), max_height))
			horiz_offset = 0
			for i in letter_images:
				whole_transcription_image.paste(i, (horiz_offset, 0))
				horiz_offset += i.size[0]

			whole_transcription_image = whole_transcription_image.convert('L')
			whole_transcription_image = whole_transcription_image.point(lambda x: 0 if x < 128 else 255, '1')

			def generateFilename():
				return hex(getrandbits(128))[2:] + ".png"

			transc_filename = path.join(TRANSCRIPTION_LETTER_CACHE_PATH, generateFilename())
			whole_transcription_image.save(transc_filename)

			return transc_filename

if __name__ == '__main__':
	# tests
	print(dictQuery("Verkehr", 3))
