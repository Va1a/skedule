import datetime as dt
from datetime import datetime
from datetime import timedelta
import copy
import pytz

def getLocalizedTime():
	tz = pytz.timezone('US/Pacific')
	return datetime.now(tz)

def deepCopyDict(dictionary):
	return copy.deepcopy(dictionary)

def ymdToDateTime(ymd):
	try:
		return datetime.strptime(ymd, '%Y-%m-%d')
	except (ValueError, TypeError):
		return None

def ymdhmToDateTime(ymdhm):
	try:
		return datetime.strptime(ymdhm, '%Y-%m-%d-%H%M')
	except (ValueError, TypeError):
		return None

def oneWeekPrior(date_time):
	return date_time - timedelta(days=7)

def oneWeekLater(date_time):
	return date_time + timedelta(days=7)

def addToTime(date_time, days=0, hours=0, minutes=0, seconds=0):
	return date_time + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

def daysOfCalendarWeek(date_time):
	days = []
	start = date_time - timedelta(days=date_time.weekday())
	for i in range(7):
		days.append(start + timedelta(days=i))
	return days

def getWeek(startTime):
	return [startTime + dt.timedelta(days=i) for i in range(7)]

def getDayName(num):
	return {0:'Monday', 1:'Tuesday', 2:'Wednesday', 3:'Thursday', 4:'Friday', 5:'Saturday', 6:'Sunday'}[num]