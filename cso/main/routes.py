from flask import render_template, send_from_directory, Blueprint, abort, flash, redirect, request, url_for
from flask_login import login_user, current_user, logout_user, login_required
from cso import db, bcrypt
from cso.models import User, Day, Shift, Assignment
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
@login_required
def viewShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	assignment = Assignment.query.filter_by(shift=shift, user=current_user).first()
	cancellable = False
	requestable = True
	if assignment:
		requestable = False
		if assignment.request == True:
			cancellable = True
	return render_template('shift.html', shift=shift, requestable=requestable, cancellable=cancellable)

@main.route('/schedule/shift/<int:shift_id>/request', methods=['POST'])
@login_required
def requestShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	if Assignment.query.filter_by(shift=shift, user=current_user).first():
		flash('You already have a request/assignment for this shift.', 'danger')
	else:
		request = Assignment(user=current_user, shift=shift, confirmed=True, request=True)
		db.session.add(request)
		db.session.commit()
		flash('Shift request submitted.', 'success')
	return redirect(url_for('main.viewShift', shift_id=shift.id))

@main.route('/schedule/shift/<int:shift_id>/remove-request', methods=['POST'])
@login_required
def removeShiftRequest(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	assignment = Assignment.query.filter_by(shift=shift, user=current_user).first()
	if not assignment:
		flash('You do not have a pending request for this shift.', 'danger')
	else:
		db.session.delete(assignment)
		db.session.commit()
		flash('Shift request removed.', 'success')
	return redirect(url_for('main.viewShift', shift_id=shift.id))

@main.route('/schedule')
@login_required
def schedule():
	unavail = False
	inputWeekOf = request.args.get('week')
	highlight = request.args.get('hl')
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
	return render_template('schedule.html', unavail=unavail, highlight=highlight, weekdays=weekdays, weekOf=weekOf, days=days, owp=oneWeekPrior(weekOf), owl=oneWeekLater(weekOf), hours=[str(i).zfill(4) for i in range(800, 2400, 100)])

@main.route('/static/<path:path>')
def staticFiles(path):
	return send_from_directory('static', path)