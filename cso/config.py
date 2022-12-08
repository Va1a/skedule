import os


class Config:
	SECRET_KEY = 'hi' #os.environ.get('crytter-secret-key')
	#SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
	SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
	RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA-PUBLIC-KEY')
	RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA-SECRET-KEY')
	RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}
	PREFERRED_URL_SCHEME = 'https'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	# MAIL_SERVER = 'smtp.sendgrid.net'
	# MAIL_PORT = 587
	# MAIL_USE_TLS = True
	# MAIL_USERNAME = os.environ.get('crytter-mail-user')
	# MAIL_PASSWORD = os.environ.get('crytter-mail-password')
