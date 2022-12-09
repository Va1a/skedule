from flask import render_template, send_from_directory, Blueprint, request, flash, abort, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from cso import db, bcrypt
from cso.models import User, Day, Shift
from cso.admin.forms import NewWeekScheduleForm, DeleteWeekScheduleForm, EditShiftForm, AddShiftForm, DeleteShiftForm
from cso.utils import getPacificTime, getWeek, getDayName, daysOfCalendarWeek, oneWeekPrior, oneWeekLater, ymdToDateTime, ymdhmToDateTime, addToTime, deepCopyDict

admin = Blueprint('admin', __name__)

@admin.route('/schedule/configure', methods=['GET', 'POST'])
@login_required
def configureSchedule():
	newWeekScheduleForm = NewWeekScheduleForm()
	deleteWeekScheduleForm = DeleteWeekScheduleForm()
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

	if newWeekScheduleForm.submitNewWeek.data and newWeekScheduleForm.validate():
	#if newWeekScheduleForm.validate_on_submit():
		for day in calendarWeek:
			dayRow = Day.query.filter_by(date=day.date()).first()
			if not dayRow:
				newDay = Day(name=day.date().strftime('%m/%d/%Y'), date=day.date())
				db.session.add(newDay)
				db.session.commit()
		flash('Schedule created for the week of '+weekOf.strftime('%B %d, %Y'), 'success')
		return redirect(url_for('admin.configureSchedule', week=weekOf.strftime('%Y-%m-%d')))

	elif deleteWeekScheduleForm.submitDeleteWeek.data and deleteWeekScheduleForm.validate():
	#elif deleteWeekScheduleForm.validate_on_submit():
		for day in calendarWeek:
			dayRow = Day.query.filter_by(date=day.date()).first()
			if dayRow:
				db.session.delete(dayRow)
				db.session.commit()
		flash('Schedule deleted for the week of '+weekOf.strftime('%B %d, %Y'), 'success')
		return redirect(url_for('admin.configureSchedule', week=weekOf.strftime('%Y-%m-%d')))

	#{'name': '', 'timeStart': '', 'timeEnd': '', 'employees': []}

	return render_template('configure_schedule.html', deleteWeekScheduleForm=deleteWeekScheduleForm,newWeekScheduleForm=newWeekScheduleForm, unavail=unavail, weekdays=weekdays, weekOf=weekOf, days=days, owp=oneWeekPrior(weekOf), owl=oneWeekLater(weekOf), hours=[str(i).zfill(4) for i in range(800, 2400, 100)])

@admin.route('/schedule/configure/add-shift', methods=['GET', 'POST'])
@login_required
def addShift():
	inputDateTime = request.args.get('datetime')
	dateTime = ymdhmToDateTime(inputDateTime)
	if not dateTime: abort(404)
	if not Day.query.filter_by(date=dateTime.date()).first(): abort(404)

	form = AddShiftForm()
	
	if form.validate_on_submit():
		startTime = ymdhmToDateTime(dateTime.strftime('%Y-%m-%d-')+form.startTime.data)
		if not startTime:
			flash('Invalid Start DateTime!', 'danger')
			return redirect(url_for('admin.addShift', datetime=inputDateTime))

		day = Day.query.filter_by(date=dateTime.date()).first()
		shift = Shift(name=form.shiftName.data, startTime=startTime, duration=form.duration.data,
			maxEmployees=form.maxEmployees.data, minEmployees=form.minEmployees.data, day_id=day.id
		)
		db.session.add(shift)
		db.session.commit()
		if form.employees.data:
			empToAdd = form.employees.data.replace(' ', '').split(',')
			for emp in empToAdd:
				if not emp.isdigit():
					flash('Invalid Employee List!', 'danger')
					return redirect(url_for('admin.addShift', datetime=inputDateTime))
				employee = User.query.filter_by(csoid=emp).first()
				if not employee:
					flash(f'Employee "{emp}" not found!', 'danger')
					return redirect(url_for('admin.addShift', datetime=inputDateTime))
				shift.employees.append(employee)
				db.session.commit()

		flash('Shift Added!', 'success')
		return redirect(url_for('admin.configureSchedule', week=dateTime.date()))
	form.startTime.data = dateTime.strftime('%H%M')
	return render_template('add_shift.html', form=form, startDate=dateTime.strftime('%m/%d/%Y'), startTime=form.startTime.data)

@admin.route('/schedule/configure/shift/<int:shift_id>', methods=['GET', 'POST'])
@login_required
def editShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	date = shift.day.date
	form = EditShiftForm()
	deleteShiftForm = DeleteShiftForm()

	if request.method == 'GET':
		form.shiftName.data = shift.name
		form.startTime.data = shift.startTime.strftime('%H%M')
		form.duration.data = str(shift.duration).zfill(4)
		form.maxEmployees.data = shift.maxEmployees
		form.minEmployees.data = shift.minEmployees
		form.employees.data = ', '.join([str(employee.csoid) for employee in shift.employees])

	if form.validate_on_submit():
		shift.name = form.shiftName.data
		startTime = ymdhmToDateTime(date.strftime('%Y-%m-%d-')+form.startTime.data)
		shift.startTime = startTime
		shift.duration = form.duration.data
		shift.maxEmployees = form.maxEmployees.data
		shift.minEmployees = form.minEmployees.data

		if form.employees.data:
			empToAdd = form.employees.data.replace(' ', '').split(',')
			for emp in empToAdd:
				if not emp.isdigit():
					flash('Invalid Employee List!', 'danger')
					return redirect(url_for('admin.editShift', shift_id=shift.id))
				employee = User.query.filter_by(csoid=emp).first()
				if not employee:
					flash(f'Employee "{emp}" not found!', 'danger')
					return redirect(url_for('admin.editShift', shift_id=shift.id))
				shift.employees.append(employee)
				db.session.commit()
		else:
			shift.employees.clear()

		db.session.commit()
		flash('Shift Updated!', 'success')
		return redirect(url_for('admin.configureSchedule', week=date))

	return render_template('edit_shift.html', shift_id=shift_id, form=form, deleteShiftForm=deleteShiftForm, startDate=date.strftime('%m/%d/%Y'))

@admin.route('/schedule/configure/shift/<int:shift_id>/delete', methods=['POST'])
@login_required
def deleteShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	url = url_for('admin.configureSchedule', week=shift.day.date.strftime('%Y-%m-%d'))
	flash(f'Shift "{shift.name}" Deleted!', 'success')
	db.session.delete(shift)
	db.session.commit()
	
	return redirect(url)

