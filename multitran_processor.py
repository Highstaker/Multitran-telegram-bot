import requests

def message_result(request, lang):
	return request


def getMultitranPage(word, lang, from_russian=False):
	"""Processes the Multitran page. Returns the status code and content."""
	if from_russian:
		page_url = 'http://www.multitran.ru/c/m.exe?l1=2&l2={0}&s={1}'.format(lang, word)
	else:
		page_url = 'http://www.multitran.ru/c/m.exe?l1={0}&s={1}'.format(lang, word)

	req = requests.get(page_url)

	return req.status_code, req.content



# class MultitranProcessor(object):
# 	"""docstring for MultitranProcessor"""
# 	def __init__(self):
# 		super(MultitranProcessor, self).__init__()
#
#
