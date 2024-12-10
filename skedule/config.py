from dotenv import load_dotenv
import os

load_dotenv()


class Config:
	SECRET_KEY = os.environ.get('SKEDULE_SECRET_KEY')
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://') if os.environ.get('DATABASE_URL') else 'none'
	RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
	RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')
	RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}
	PREFERRED_URL_SCHEME = 'https'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	# MAIL_SERVER = 'smtp.sendgrid.net'
	# MAIL_PORT = 587
	# MAIL_USE_TLS = True
	# MAIL_USERNAME = os.environ.get('crytter-mail-user')
	# MAIL_PASSWORD = os.environ.get('crytter-mail-password')
