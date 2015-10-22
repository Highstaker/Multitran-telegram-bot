#!/usr/bin/python3

#this is a LIBRARY

# from urllib.request import urlopen
import requests

def getHTML(url,repeat_on_failure=True):

	while True:
		try:
			# sock = urlopen(url)
			htmlSource = requests.get(url)
		except Exception as e:#using wildcard except is a bad coding style 
			print("Error: " + str(e))
			if repeat_on_failure:
				pass
			else:
				break
		else:
			break
	# htmlSource = sock.read()
	# sock.close()

	return htmlSource.content

def getHTML_UTF8(url,method="strict"):
	return getHTML(url).decode('utf-8',method)

def getHTML_specifyEncoding(url,encoding='utf-8',method='strict'):
	return getHTML(url).decode(encoding,method)

def getEncoding(url,repeat_on_failure=True):
	'''
	Doesn't work!
	'''
	# while True:
	# 	try:
	# 		sock = urllib.request.urlopen(url)
	# 	except:#using wildcard except is a bad coding style 
	# 		if repeat_on_failure:
	# 			pass
	# 		else:
	# 			break
	# 	else:
	# 		break

	# return fp.headers.getparam('charset')