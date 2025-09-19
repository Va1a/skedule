from flask import render_template, send_from_directory, Blueprint, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from skedule import db, bcrypt
from skedule.models import User, Day
from skedule.users.forms import LoginForm, RegisterForm

users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.home'))
	form = RegisterForm()
	if form.validate_on_submit():
		hashedpw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(name=form.name.data, email=form.email.data, phone=form.phone.data, password=hashedpw)
		db.session.add(user)
		db.session.commit()
		flash(f'Account created, you may now log in.', 'success')
		return redirect(url_for('users.login'))
	return render_template('register.html', form=form)


@users.route('/login', methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			nextpage = request.args.get('next')
			flash(f'Logged in as EMP {user.external_id}.', 'success')
			return redirect(nextpage) if nextpage else redirect(url_for('main.home'))
		else:
			flash('Invalid credentials.', 'danger')
	return render_template('login.html', form=form)

@users.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.', 'success')
	return redirect(url_for('users.login'))
