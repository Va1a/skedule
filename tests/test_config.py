class TestConfig:
  SECRET_KEY = 'Testing'
  TESTING = True
  SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
  RECAPTCHA_PUBLIC_KEY = None
  RECAPTCHA_PRIVATE_KEY = None
  RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}
  PREFERRED_URL_SCHEME = 'https'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
