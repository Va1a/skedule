from pathlib import Path

from skedule import bcrypt, create_app, db
from skedule.config import Config
from skedule.models import Template, User


SEED_USERS = [
    {
        "id": 1,
        "external_id": "1",
        "name": "Vala Skedule",
        "email": "vala@skedule.net",
        "phone": "8185551234",
    },
    {
        "id": 2,
        "external_id": "2",
        "name": "Sam Sepiol",
        "email": "sam@skedule.net",
        "phone": "8183224172",
    },
    {
        "id": 3,
        "external_id": "3",
        "name": "Dolores Haze",
        "email": "haze@skedule.net",
        "phone": "8052123644",
    },
]

SEED_TEMPLATES = [
    {
        "name": "Test",
        "startTime": "0800",
        "duration": 500,
        "maxEmployees": 1,
        "minEmployees": 1,
    },
]


class LocalDevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///site.db"


def create_local_app():
    return create_app(LocalDevelopmentConfig)


def ensure_instance_path(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def get_local_database_path(app):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    sqlite_prefix = "sqlite:///"
    if not uri.startswith(sqlite_prefix):
        raise ValueError("Local development database is not configured for SQLite.")

    raw_path = uri.removeprefix(sqlite_prefix)
    if raw_path.startswith("/"):
        return Path(raw_path)
    return Path(app.instance_path) / raw_path


def ensure_local_database(app):
    ensure_instance_path(app)

    with app.app_context():
        db.create_all()

        created_users = 0
        created_templates = 0
        hashed_password = bcrypt.generate_password_hash("test").decode("utf-8")
        for user_data in SEED_USERS:
            if User.query.filter_by(email=user_data["email"]).first():
                continue
            user = User(password=hashed_password, **user_data)
            db.session.add(user)
            created_users += 1

        for template_data in SEED_TEMPLATES:
            if Template.query.filter_by(name=template_data["name"]).first():
                continue
            template = Template(**template_data)
            db.session.add(template)
            created_templates += 1

        db.session.commit()

        return {
            "table_names": db.inspect(db.engine).get_table_names(),
            "seeded_users": created_users,
            "seeded_templates": created_templates,
        }
