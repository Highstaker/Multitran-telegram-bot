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
		# print(data)#debug

		unique_users = {i[1] for i in data}
		n_unique_users = len(unique_users)
		print("unique_users", n_unique_users)

		# convert unix times to time structures
		timestructs = (gmtime(i[0]) for i in data)
		# group the structures by hour and date.
		# Get an array of tuples ( (hour, day, month, year), number of ticks in the period))
		grouped_ticks = tuple((t, sum(1 for i in ticks)) for t, ticks in
						groupby(timestructs, key=lambda x: datetime(hour=x.tm_hour,
																	day=x.tm_mday,
																	month=x.tm_mon,
																	year=x.tm_year)))


		# print("timestructs", list(timestructs))#debug
		# print(sum(1 for i in grouped_ticks))#debug
		# print("grouped_ticks", list(grouped_ticks))#debug

		from matplotlib import dates
		# floats representing times on x axit in pyplot format
		times = tuple(dates.date2num(i[0]) for i in grouped_ticks)
		# number of user activities. Represented on Y axis
		activities = tuple(i[1] for i in grouped_ticks)

		# print("times", times)#debug
		# print("activities", activities)#debug

		import matplotlib
		# Force matplotlib to not use any Xwindows backend.
		# matplotlib.use('Agg')
		matplotlib.use('TkAgg')
		import matplotlib.pyplot as plt

		def calculateImageSize(f, data, min_distance=0.1, scale=1):
			"""Calculates the size of image based on number of dots and minimum allowed distance between them.
			The result can be assigned to `fig.set_size_inches`"""
			fig_size = f.get_size_inches()
			# print("fig_size", fig_size)#debug [ 8. 6. ]
			n_points = len(data)  # amount of points on graph
			new_x_size = max(fig_size[0], min_distance * n_points)

			return new_x_size*scale, fig_size[1]*scale

		fig, ax = plt.subplots()  # create figure & 1 axis
		ax.plot_date(times, activities, 'k')  # line graph
		ax.plot_date(times, activities, 'bo')  # dots graph
		ax.xaxis.set_major_locator(dates.DayLocator())
		ax.xaxis.set_major_formatter(dates.DateFormatter('%D'))
		ax.tick_params(direction='out', pad=10)
		ax.xaxis.set_minor_locator(dates.HourLocator())
		ax.xaxis.set_minor_formatter(dates.DateFormatter('%H'))
		for tick in ax.xaxis.get_minor_ticks():
			tick.label.set_fontsize(5)
		fig.autofmt_xdate()

		# set image size
		fig.set_size_inches(*calculateImageSize(fig, times, min_distance=1, scale=1))
		plt.title("User activity over time\n Unique users so far: {0}".format(n_unique_users))
		plt.xlabel('Time')
		plt.ylabel('User activity')
		plt.subplots_adjust(bottom=.2)
		plt.grid(b=True, which="major", color="r", linestyle='-')
		plt.grid(b=True, which="minor", color="g", linestyle='--')
		# plt.show()
		savefilename = '001.png'
		fig.savefig(savefilename)
		plt.close(fig)

if __name__ == '__main__':
	ActivityLogger().visualizeTicks()