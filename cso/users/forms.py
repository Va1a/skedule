from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from flask_wtf.file import FileField, FileAllowed
from wtforms import IntegerField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError, Optional, NumberRange
from flask_login import current_user
from cso.models import User

class RegisterForm(FlaskForm):
	csoid = IntegerField('CSO Number/ID', validators=[DataRequired(), NumberRange(min=0, max=100)])
	name = StringField('Name', validators=[DataRequired(), Length(min=1, max=300)])
	email = StringField('Email', validators=[
		DataRequired(), Length(min=1, max=256)
		])
	phone = StringField('Phone Number', validators=[DataRequired(), Length(min=1, max=20)])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=256)])
	confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match!')])
	submit = SubmitField('Register')

	def validate_csoid(self, csoid):
		user = User.query.filter_by(csoid=csoid.data).first()
		if user:
			raise ValidationError('An account with this CSO ID has already been registered')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('An account with this email has already been registered')

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[
		DataRequired(), Length(min=1, max=256)
		])
	password = PasswordField('Password', validators=[
		DataRequired()
		])
	remember = BooleanField('Stay logged in?')
	# recaptcha = RecaptchaField(validators=[Recaptcha(message="Prove you are not a robot.")])

	submit = SubmitField('Log In')