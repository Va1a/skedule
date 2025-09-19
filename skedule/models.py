from skedule import db, login_manager
from flask import current_app
from skedule.utils import getLocalizedTime
from flask_login import UserMixin
import json
import uuid

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

user_shiftTemplate = db.Table('user_shiftTemplate',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
	db.Column('template_id', db.Integer, db.ForeignKey('template.id', ondelete='CASCADE'))
)

class Assignment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
	shift_id = db.Column(db.Integer, db.ForeignKey('shift.id', ondelete='CASCADE'))
	request = db.Column(db.Boolean, nullable=False, default=False)
	confirmed = db.Column(db.Boolean, nullable=False, default=False)
	assignment_type = db.Column(db.String(32), nullable=False, default='regular')
	date_created = db.Column(db.DateTime, nullable=False, default=getLocalizedTime)

	def render(self):
		render = ''
		if self.request:
			render += '(REQ)'
		typeDict = {'regular': '', 'ride-along': '(R)', 'trainee': '(T)', 'covering': '(C)', 'probationary': '(P)'}
		render += (typeDict[self.assignment_type])
		if not self.confirmed:
			render += '(A)'
		return render

	def colorize(self):
		if not self.confirmed:
			return '#0000f5'
		if self.request:
			return '#cfc102'
		colors = {'regular': '#000000', 'ride-along': '#982ff4', 'trainee': '#f19e38', 'covering': '#ea3728', 'probationary': '#000000'}
		return colors[self.assignment_type]

	def toJSON(self):
		return {'id': self.id, 'user': self.user_id, 'shift': self.shift_id, 'request': self.request,
		'confirmed': self.confirmed, 'assignment_type': self.assignment_type, 'suffix': self.render(),
		'color': self.colorize(), 'date_created': self.date_created.strftime('%Y-%m-%d-%H%M')}

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	oauth_id = db.Column(db.String(512), nullable=True, unique=True)
	_external_id = db.Column(db.String(256), nullable=True, unique=True)
	name = db.Column(db.String(300), nullable=False)
	email = db.Column(db.String(256), unique=True, nullable=False)
	phone = db.Column(db.String(20), nullable=False)
	date_joined = db.Column(db.DateTime, nullable=False, default=getLocalizedTime)
	password = db.Column(db.String(60), nullable=False)
	meta = db.Column(db.JSON, nullable=False, default={})

	assignments = db.relationship(Assignment, backref='user', cascade='all, delete-orphan')
	shiftTemplates = db.relationship('Template', secondary=user_shiftTemplate, backref='employees', cascade='all')

	@property
	def external_id(self):
		return self._external_id if self._external_id else self.id
	

	def toJSON(self):
		return {'id': self.id, 'name': self.name, 'date_joined': self.date_joined.strftime('%Y-%m-%d-%H%M'),
		'external_id': self.external_id, 'email': self.email, 'phone': self.phone, 'meta': self.meta
		}

class Shift(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), nullable=False)
	startTime = db.Column(db.DateTime, nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	maxEmployees = db.Column(db.Integer, nullable=False)
	minEmployees = db.Column(db.Integer, nullable=False)
	day_id = db.Column(db.Integer, db.ForeignKey('day.id'), nullable=False)

	assignments = db.relationship(Assignment, backref='shift', cascade='all, delete-orphan')

	def toJSON(self):
		assignments_json = db.session.query(Assignment.id, Assignment.assignment_type).filter_by(shift_id=self.id).all()
		return {'id': self.id, 'name': self.name, 'startTime': self.startTime.strftime('%Y-%m-%d-%H%M'), 'duration': str(self.duration).zfill(4),
		'maxEmployees': self.maxEmployees, 'minEmployees': self.minEmployees, 'day_id': self.day_id,
		'assignments': [{'id': assignment.id, 'type': assignment.assignment_type} for assignment in assignments_json]
		}

class Template(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	maxEmployees = db.Column(db.Integer, nullable=False)
	minEmployees = db.Column(db.Integer, nullable=False)
	startTime = db.Column(db.String(4), nullable=False)

	def toJSON(self):
		return {'id': self.id, 'name': self.name, 'startTime': self.startTime, 
		'maxEmployees': self.maxEmployees, 'minEmployees': self.minEmployees,
		'duration': str(self.duration).zfill(4), 'employees': [emp.external_id for emp in self.employees]}

class Day(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), nullable=False)
	date = db.Column(db.Date, nullable=False, unique=True)
	shifts = db.relationship('Shift', backref='day', lazy=True)
	data = db.Column(db.JSON, nullable=False, default={})

	def toJSON(self):
		return {'id': self.id, 'name': self.name, 'date': self.date.strftime('%Y-%m-%d'),
		'shifts': [{'id': shift.id, 'name': shift.name, 'startTime': shift.startTime.strftime('%H%M')} for shift in self.shifts]
		}
