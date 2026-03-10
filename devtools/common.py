from skedule import create_app
from skedule.config import Config


class LocalDevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///site.db"


def create_local_app():
    return create_app(LocalDevelopmentConfig)
