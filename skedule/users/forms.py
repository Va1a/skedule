from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from skedule.models import User


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=300)])
    email = StringField("Email", validators=[DataRequired(), Length(min=1, max=256)])
    phone = StringField(
        "Phone Number", validators=[DataRequired(), Length(min=1, max=20)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=1, max=256)]
    )
    confirm = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match!")],
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "An account with this email has already been registered"
            )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(min=1, max=256)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Stay logged in?")
    submit = SubmitField("Log In")
