from flask import render_template, send_from_directory, Blueprint, request, flash, abort, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from skedule import db, bcrypt
from skedule.models import User, Day, Shift, Template, Assignment
from skedule.utils import ymdhmToDateTime, ymdToDateTime

api = Blueprint('api', __name__)

@api.before_request
def beforeApiRequests():
	if not current_user.is_authenticated:
		abort(404)

@api.route('/api/shift/<int:shift_id>')
def apiShift(shift_id):
	shift = Shift.query.get_or_404(shift_id)
	return shift.toJSON()

@api.route('/api/assignment/<int:assignment_id>')
def apiAssignment(assignment_id):
	assignment = Assignment.query.get_or_404(assignment_id)
	return assignment.toJSON()

@api.route('/api/assignment/byUser/<int:user_id>')
def apiUserAssignment(user_id):
	assignments = Assignment.query.filter_by(user_id=user_id).all()
	return {'ids': [assignment.id for assignment in assignments]}

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

@api.route('/api/user/byExternalID/<int:external_id>')
def apiUserExternal(external_id):
	user = User.query.filter_by(external_id=external_id).first_or_404()
	return redirect(url_for('api.apiUser', user_id=user.id))

@api.route('/api/user/<int:user_id>')
def apiUser(user_id):
	user = User.query.get_or_404(user_id)
	return user.toJSON()

@api.route('/api/assignment/<int:assignment_id>/update', methods=['POST'])
def apiUpdateAssignment(assignment_id):
	assignment = Assignment.query.get_or_404(assignment_id)
	data = request.json
	assignment.request = data['request']
	assignment.confirmed = data['confirmed']
	assignment.assignment_type = data['assignment_type']
	db.session.commit()
	return assignment.toJSON()
