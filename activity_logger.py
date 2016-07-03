from os import path, makedirs
from datetime import datetime
from calendar import timegm # this function utilizes UTC, not local time, unlike time.mktime
from time import gmtime
from itertools import groupby

from textual_data import SCRIPT_FOLDER

LOG_DIRNAME = "logs"


class ActivityLogger(object):
	"""docstring for ActivityLogger"""
	def __init__(self):
		super(ActivityLogger, self).__init__()

		makedirs(LOG_DIRNAME, exist_ok=True)
		self.logfile = path.join(SCRIPT_FOLDER, LOG_DIRNAME, "multitran_useractivity.log")

	def tick(self, chat_id):
		with open(self.logfile, "a") as f:
			cur_utc_time = timegm(datetime.utcnow().timetuple())
			msg = " ".join(map(str, [cur_utc_time, chat_id])) + "\n"
			f.write(msg)

	def visualizeTicks(self):
		# read the data from file
		with open(self.logfile, "r") as f:
			data = f.read()
		data = tuple(tuple(map(int, i.split(" "))) for i in data.split("\n") if i)
		print(data)#debug

		unique_users = {i[1] for i in data}
		print("unique_users", len(unique_users))

		# for i in data:
		# 	unix_time = i[0]
		# 	timestruct = gmtime(unix_time)
		# 	print(timestruct)

		# convert unix times to time structures
		timestructs = (gmtime(i[0]) for i in data)
		# group the structures by hour and date.
		# Get an array of tuples ( (hour, day, month, year), number of ticks in the period))
		grouped_ticks = tuple((t, sum(1 for i in ticks)) for t, ticks in
						groupby(timestructs, key=lambda x: (x.tm_hour, x.tm_mday, x.tm_mon, x.tm_year)))



		# print(sum(1 for i in grouped_ticks))#debug
		# print(list(grouped_ticks))#debug

		times = tuple(i[0][0] for i in grouped_ticks)
		activities = tuple(i[1] for i in grouped_ticks)

		print("grouped_ticks", grouped_ticks)#debug
		print("times", times)#debug
		print("activities", activities)#debug

		# import matplotlib
		# from matplotlib import dates
		# # Force matplotlib to not use any Xwindows backend.
		# matplotlib.use('Agg')
		# import matplotlib.pyplot as plt
		# fig, ax = plt.subplots()  # create figure & 1 axis
		# ax.plot(times, activities, 'k', times, activities, 'bo')
		# ax.xaxis.set_major_formatter(dates.DateFormatter('%y/%m/%d %H:%M'))
		# plt.title("User activity over time")
		# plt.xlabel('Time')
		# plt.ylabel('User activity')
		# plt.grid(True)
		# savefilename = '001.png'
		# fig.savefig(savefilename)
		# plt.close(fig)

if __name__ == '__main__':
	ActivityLogger().visualizeTicks()