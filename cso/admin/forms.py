from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField, HiddenField, DateTimeField, DateField, TimeField, StringField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError, Optional, NumberRange
from flask_login import current_user

class NewWeekScheduleForm(FlaskForm):
	nhide = HiddenField('NewWeekCreate', validators=[])
	submitNewWeek = SubmitField('Create Schedule')

class DeleteWeekScheduleForm(FlaskForm):
	dhide = HiddenField('WeekDelete', validators=[])
	submitDeleteWeek = SubmitField('Delete Schedule')

class DeleteShiftForm(FlaskForm):
	submit = SubmitField('Delete Shift')

class AddShiftForm(FlaskForm):
	shiftName = StringField('Shift Name:', validators=[DataRequired(), Length(1, 128)])
	startTime = StringField('Start Time:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	duration = StringField('Duration:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	maxEmployees = IntegerField('Maximum # of Employees:', validators=[DataRequired()])
	minEmployees = IntegerField('Minimum # of Employees:', validators=[DataRequired()])
	employees = StringField('Assign Employees:', validators=[Optional(), Length(0, 512), Regexp(r'^[1-9]\d(?:, {0,1}[1-9]\d)*$', message='Input must be a comma seperated list of CSO IDs.')])
	submit = SubmitField('Add Shift')

	def validate_maxEmployees(self, maxEmployees):
		if maxEmployees.data < self.minEmployees.data:
			raise ValidationError('Maximum employee count cannot be less than the minimum!')

class AddTemplateForm(FlaskForm):
	shiftName = StringField('Template Name:', validators=[DataRequired(), Length(1, 128)])
	startTime = StringField('Start Time:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	duration = StringField('Duration:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	maxEmployees = IntegerField('Maximum # of Employees:', validators=[DataRequired()])
	minEmployees = IntegerField('Minimum # of Employees:', validators=[DataRequired()])
	employees = StringField('Assign Employees:', validators=[Optional(), Length(0, 512), Regexp(r'^[1-9]\d(?:, {0,1}[1-9]\d)*$', message='Input must be a comma seperated list of CSO IDs.')])
	submit = SubmitField('Create Template')

	def validate_maxEmployees(self, maxEmployees):
		if maxEmployees.data < self.minEmployees.data:
			raise ValidationError('Maximum employee count cannot be less than the minimum!')

class EditTemplateForm(FlaskForm):
	shiftName = StringField('Template Name:', validators=[DataRequired(), Length(1, 128)])
	startTime = StringField('Start Time:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	duration = StringField('Duration:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	maxEmployees = IntegerField('Maximum # of Employees:', validators=[DataRequired()])
	minEmployees = IntegerField('Minimum # of Employees:', validators=[DataRequired()])
	employees = StringField('Assign Employees:', validators=[Optional(), Length(0, 512), Regexp(r'^[1-9]\d(?:, {0,1}[1-9]\d)*$', message='Input must be a comma seperated list of CSO IDs.')])
	submit = SubmitField('Save Changes')

	def validate_maxEmployees(self, maxEmployees):
		if maxEmployees.data < self.minEmployees.data:
			raise ValidationError('Maximum employee count cannot be less than the minimum!')

class EditShiftForm(FlaskForm):
	shiftName = StringField('Shift Name:', validators=[DataRequired(), Length(1, 128)])
	startTime = StringField('Start Time:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	duration = StringField('Duration:', validators=[DataRequired(), Regexp(r'^([01]\d|2[0-3])([0-5]\d)$', message='Must be in 24-hour HHMM format!')])
	maxEmployees = IntegerField('Maximum # of Employees:', validators=[DataRequired()])
	minEmployees = IntegerField('Minimum # of Employees:', validators=[DataRequired()])
	submit = SubmitField('Save Changes')

	def validate_maxEmployees(self, maxEmployees):
		if maxEmployees.data < self.minEmployees.data:
			raise ValidationError('Maximum employee count cannot be less than the minimum!')