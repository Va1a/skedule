from flask import render_template, send_from_directory, Blueprint, abort, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from cso import db, bcrypt
from cso.models import User, Day, Shift
from cso.utils import getPacificTime, getWeek, getDayName, daysOfCalendarWeek, ymdToDateTime, oneWeekLater, oneWeekPrior

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def home():
	# shifts = Shift.query.filter(employee == current_user and start_datetime > getPacificTime() and start_datetime < getWeek(getPacificTime()))
	weekdays = [{'name': getDayName(day.weekday()), 'date': day.strftime('%m/%d')} for day in getWeek(getPacificTime())]
	days = []
	for day in getWeek(getPacificTime()):
		days.append(Day.query.filter_by(date=day.date()))

	
	return render_template('dashboard.html', time=getPacificTime(), weekdays=weekdays, days=days)

@main.route('/schedule/shift/<int:shift_id>')
def viewShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	return render_template('shift.html', shift=shift)

@main.route('/schedule')
@login_required
def schedule():
	unavail = False
	inputWeekOf = request.args.get('week')
	if inputWeekOf:
		weekOf = ymdToDateTime(inputWeekOf)
		if not weekOf: abort(404)
		calendarWeek = daysOfCalendarWeek(weekOf)
	else:
		calendarWeek = daysOfCalendarWeek(getPacificTime())
	weekOf = calendarWeek[0]
	weekdays = [{'name': getDayName(day.weekday()), 'date': day.strftime('%m/%d')} for day in calendarWeek]
	days = []
	for day in calendarWeek:
		dayRow = Day.query.filter_by(date=day.date()).first()
		if dayRow:
			days.append(dayRow)
		else:
			unavail = True
	return render_template('schedule.html', unavail=unavail, weekdays=weekdays, weekOf=weekOf, days=days, owp=oneWeekPrior(weekOf), owl=oneWeekLater(weekOf), hours=[str(i).zfill(4) for i in range(800, 2400, 100)])

@main.route('/static/<path:path>')
def staticFiles(path):
	return send_from_directory('static', path)