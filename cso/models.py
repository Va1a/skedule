from cso import db, login_manager
from flask import current_app
from cso.utils import getPacificTime
from flask_login import UserMixin
import json

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

user_shift = db.Table('user_shift',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('shift_id', db.Integer, db.ForeignKey('shift.id'))
)

user_shiftTemplate = db.Table('user_shiftTemplate',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('template_id', db.Integer, db.ForeignKey('template.id'))
)

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	oauth_id = db.Column(db.String(512), nullable=False, unique=True, default='')
	csoid = db.Column(db.Integer, nullable=False, unique=True)
	name = db.Column(db.String(300), nullable=False)
	email = db.Column(db.String(256), unique=True, nullable=False)
	phone = db.Column(db.Integer, nullable=False)
	date_joined = db.Column(db.DateTime, nullable=False, default=getPacificTime)
	password = db.Column(db.String(60), nullable=False)
	meta = db.Column(db.JSON, nullable=False, default={})

	shifts = db.relationship('Shift', secondary=user_shift, backref='employees')
	shiftTemplates = db.relationship('Template', secondary=user_shiftTemplate, backref='employees')

	def toJSON(self):
		return {'id': self.id, 'name': self.name, 'date_joined': self.date_joined.strftime('%Y-%m-%d-%H%M'),
		'csoid': self.csoid, 'email': self.email, 'phone': self.phone, 'meta': self.meta
		}
	# comments = db.relationship('Comment', backref='author', lazy=True)
	# badges = db.relationship('Badge', backref='bearer', lazy=True)
	# alerts = db.relationship('Alert', backref='assoc_user', lazy=True)

class Shift(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), nullable=False)
	startTime = db.Column(db.DateTime, nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	maxEmployees = db.Column(db.Integer, nullable=False)
	minEmployees = db.Column(db.Integer, nullable=False)
	day_id = db.Column(db.Integer, db.ForeignKey('day.id'), nullable=False) 

	def toJSON(self):
		return {'id': self.id, 'name': self.name, 'startTime': self.startTime.strftime('%Y-%m-%d-%H%M'), 'duration': str(self.duration).zfill(4),
		'maxEmployees': self.maxEmployees, 'minEmployees': self.minEmployees, 'day_id': self.day_id,
		'employees': [emp.csoid for emp in self.employees]
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
		'duration': str(self.duration).zfill(4), 'employees': [emp.csoid for emp in self.employees]}

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
