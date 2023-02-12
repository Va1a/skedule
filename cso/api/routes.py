from flask import render_template, send_from_directory, Blueprint, request, flash, abort, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from cso import db, bcrypt
from cso.models import User, Day, Shift, Template
from cso.utils import ymdhmToDateTime, ymdToDateTime

api = Blueprint('api', __name__)

@api.route('/api/shift/<int:shift_id>')
def apiShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	return shift.toJSON()

@api.route('/api/template/<int:template_id>')
def apiTemplate(template_id):
	template = Template.query.get_or_404(template_id)
	return template.toJSON()

@api.route('/api/template/byName/<string:name>')
def apiTemplateName(name):
	template = Template.query.filter_by(name=name).first_or_404()
	return template.toJSON()

@api.route('/api/template/list-all')
def apiListTemplate():
	return {'templates':[{'id': template.id, 'name': template.name} for template in Template.query.all()]}

@api.route('/api/shift/byDatetime/<string:datetime>')
def apiDatetimeShift(datetime):
	datetime = ymdhmToDateTime(datetime)
	if datetime:
		shift = Shift.query.filter_by(startTime=datetime).first_or_404()
	else:
		abort(404)
	return redirect(url_for('api.apiShift', shift_id=shift.id))

@api.route('/api/day/<int:day_id>')
def apiDay(day_id):
	day = Day.query.get_or_404(day_id)
	return day.toJSON()

@api.route('/api/day/byDate/<string:date>')
def apiDateDay(date):
	date = ymdToDateTime(date).date()
	if date:
		day = Day.query.filter_by(date=date).first_or_404()
	else:
		abort(404)
	return redirect(url_for('api.apiDay', day_id=day.id))

@api.route('/api/employee/<int:cso_id>')
def apiCsoEmployee(cso_id):
	emp = User.query.filter_by(csoid=cso_id).first_or_404()
	return emp.toJSON()

@api.route('/api/employee/byIID/<int:user_id>')
def apiCsoEmployeeByInternalID(user_id):
	user = User.query.get_or_404(user_id)
	return redirect(url_for('api.apiCsoEmployee', cso_id=user.csoid))