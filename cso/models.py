from cso import db, login_manager
from flask import current_app
from cso.utils import getPacificTime
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

user_shift = db.Table('user_shift',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('shift_id', db.Integer, db.ForeignKey('shift.id'))
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

	def asJSON(self):
		return {'name': self.name, 'startTime': self.startTime, 'duration': self.duration, 
		'maxEmployees': self.maxEmployees, 'minEmployees': self.minEmployees, 
		'employees': self.employees}

class Day(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), nullable=False)
	date = db.Column(db.Date, nullable=False, unique=True)
	shifts = db.relationship('Shift', backref='day', lazy=True)
	data = db.Column(db.JSON, nullable=False, default={})
	# 'hours':{
	# 	'0000': {'shifts':[]},
	# 	'0100': {'shifts':[]},
	# 	'0200': {'shifts':[]},
	# 	'0300': {'shifts':[]},
	# 	'0400': {'shifts':[]},
	# 	'0500': {'shifts':[]},
	# 	'0600': {'shifts':[]},
	# 	'0700': {'shifts':[]},
	# 	'0800': {'shifts':[]},
	# 	'0900': {'shifts':[]},
	# 	'1000': {'shifts':[]},
	# 	'1100': {'shifts':[]},
	# 	'1200': {'shifts':[]},
	# 	'1300': {'shifts':[]},
	# 	'1400': {'shifts':[]},
	# 	'1500': {'shifts':[]},
	# 	'1600': {'shifts':[]},
	# 	'1700': {'shifts':[]},
	# 	'1800': {'shifts':[]},
	# 	'1900': {'shifts':[]},
	# 	'2000': {'shifts':[]},
	# 	'2100': {'shifts':[]},
	# 	'2200': {'shifts':[]},
	# 	'2300': {'shifts':[]}}
