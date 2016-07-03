class DictUtils:
	@staticmethod
	def replaceKey(dic, oldkey, newkey):
		try:
			dic[newkey] = dic.pop(oldkey)
		except KeyError:
			raise KeyError("Could not replace key {0}. It was not found!".format(oldkey))

	@staticmethod
	def dictGetCaseInsensitive(dic, key):
		result = None
		try:
			# maybe it already exists as-is
			result = dic[key]
		except KeyError:
			error_message = "The key was not found, even case-insensitively"
			if isinstance(key, str):
				# try to find case-insensitively
				upper_key = key.upper()
				for i in dic:
					if i.upper() == upper_key:
						result = dic[i]
						break
				else:
					raise KeyError(error_message)
			else:
				raise KeyError(error_message)

		return result
