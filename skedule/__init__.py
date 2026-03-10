import json

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from skedule.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.refresh_view = "users.login"
login_manager.needs_refresh_message = "Re-authenticate to continue..."
login_manager.needs_refresh_message_category = "warning"
login_manager.login_message = "Login to access this page..."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.jinja_env.globals.update(json=json)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from skedule.admin.routes import admin
    from skedule.api.routes import api
    from skedule.errors.handlers import errors
    from skedule.main.routes import main
    from skedule.users.routes import users

    app.register_blueprint(users)
    app.register_blueprint(admin)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(api)

    return app
