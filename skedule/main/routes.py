from flask import render_template, send_from_directory, Blueprint, abort, flash, redirect, request, url_for, g
from sqlalchemy import and_
from flask_login import login_user, current_user, logout_user, login_required
from skedule import db, bcrypt
from skedule.models import User, Day, Shift, Assignment, Alert
from skedule.utils import getLocalizedTime, getWeek, getDayName, daysOfCalendarWeek, ymdToDateTime, oneWeekLater, oneWeekPrior

main = Blueprint('main', __name__)

@main.before_app_request
def load_unseen_notifications():
	if current_user.is_authenticated:
		g.unseen_notifications_count = Alert.query.filter_by(
			recipient_user_id=current_user.id, 
			seen=False
		).count()
	else:
		g.unseen_notifications_count = 0

@main.route('/')
@login_required
def home():
	current_week = getWeek(getLocalizedTime())
	weekdays = [{'name': getDayName(day.weekday()), 'date': day.strftime('%m/%d')} for day in current_week]
	start_date = current_week[0].date()
	end_date = current_week[-1].date()
	
	# Get all days for the week in one query
	days_dict = {day.date: day for day in Day.query.filter(Day.date.between(start_date, end_date)).all()}
	days = [days_dict.get(d.date()) for d in current_week]
	
	# Get all user assignments for the week in one efficient query
	user_assignments = Assignment.query.join(Shift).join(Day).filter(
		Assignment.user_id == current_user.id,
		Day.date.between(start_date, end_date)
	).all()
	
	user_shifts = []
	user_shift_ids = set()
	for ua in user_assignments:
		day_dt = ua.shift.day.date
		user_shift_ids.add(ua.shift.id)
		user_shifts.append({
			'shift': ua.shift,
			'assignment': ua,
			'day_name': getDayName(day_dt.weekday()),
			'date': day_dt.strftime('%m/%d'),
			'time': ua.shift.startTime.strftime('%-I:%M %p')
		})
	
	# Calculate total shifts for the week
	total_shifts = sum(len(day.shifts) if day else 0 for day in days)
	
	return render_template(
		'dashboard.html',
		time=getLocalizedTime(),
		weekdays=weekdays,
		days=days,
		user_shifts=user_shifts,
		user_shift_ids=user_shift_ids,
		total_shifts=total_shifts,
	)

@main.route('/schedule/shift/<int:shift_id>')
@login_required
def viewShift(shift_id):
	shift = db.get_or_404(Shift, shift_id)
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
	shift = db.get_or_404(Shift, shift_id)
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
	shift = db.get_or_404(Shift, shift_id)
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
		calendarWeek = daysOfCalendarWeek(getLocalizedTime())
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

@main.route('/upcoming')
@login_required
def upcoming():
	page = request.args.get('page', 1, type=int)
	no_pending = request.args.get('no-pending', False, type=bool)
	per_page = 10
	
	# Get user's upcoming shifts (from today onwards, both confirmed and pending)
	today = getLocalizedTime().date()
	upcoming_assignments = Assignment.query.join(Shift).join(Day).filter(
		and_(Assignment.user_id == current_user.id, Assignment.request == False if no_pending else True),
		Day.date >= today
	).order_by(Shift.startTime.asc()).paginate(
		page=page, per_page=per_page, error_out=False
	)
	
	return render_template('upcoming.html', assignments=upcoming_assignments, no_pending=no_pending)

@main.route('/pending-requests')
@login_required
def pendingRequests():
	page = request.args.get('page', 1, type=int)
	per_page = 10
	
	# Get user's pending requests (request=True)
	pending_assignments = Assignment.query.join(Shift).join(Day).filter(
		and_(Assignment.user_id == current_user.id, Assignment.request == True)
	).order_by(Shift.startTime.asc()).paginate(
		page=page, per_page=per_page, error_out=False
	)
	
	return render_template('pending_requests.html', assignments=pending_assignments)

@main.route('/roster')
@login_required
def roster():
	users = User.query.all()
	return render_template('roster.html', users=users)

@main.route('/alerts')
@login_required
def notifications():
	page = request.args.get('page', 1, type=int)
	per_page = 20
	
	# Get user's alerts, ordered by timestamp (newest first)
	alerts = Alert.query.filter_by(recipient_user_id=current_user.id).order_by(
		Alert.timestamp.desc()
	).paginate(page=page, per_page=per_page, error_out=False)
	
	# Store which alerts were unseen before marking them as seen
	unseen_alert_ids = {alert.id for alert in alerts.items if not alert.seen}
	
	# Mark the alerts on this page as seen
	alert_ids = [alert.id for alert in alerts.items]
	if alert_ids:
		Alert.query.filter(Alert.id.in_(alert_ids), Alert.seen == False).update(
			{'seen': True}, synchronize_session=False
		)
		db.session.commit()
	
	return render_template('notifications.html', alerts=alerts, unseen_alert_ids=unseen_alert_ids)

@main.route('/alerts/<int:alert_id>/dismiss', methods=['POST'])
@login_required
def dismiss_alert(alert_id):
	alert = db.get_or_404(Alert, alert_id)
	
	# Ensure user can only dismiss their own alerts
	if alert.recipient_user_id != current_user.id:
		abort(403)
	
	db.session.delete(alert)
	db.session.commit()
	flash('Alert dismissed.', 'success')
	
	return redirect(url_for('main.notifications'))

@main.route('/static/<path:path>')
def staticFiles(path):
	return send_from_directory('static', path)
