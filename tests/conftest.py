from datetime import datetime

import pytest

from skedule import bcrypt, create_app, db
from skedule.models import Alert, Assignment, Day, Feature, LogEntry, LogField, Shift, User
from tests.test_config import TestConfig


class AppTestConfig(TestConfig):
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(config_class=AppTestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login_user(client):
    def do_login(user, password=None):
        response = client.post(
            "/login",
            data={
                "email": user.email,
                "password": password or user.plaintext_password,
                "submit": "Log In",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        return response

    return do_login


@pytest.fixture
def user_factory(app):
    def factory(**overrides):
        index = User.query.count() + 1
        password = overrides.pop("password", "test_password")
        user = User(
            name=overrides.pop("name", f"Test User {index}"),
            email=overrides.pop("email", f"user{index}@test.com"),
            phone=overrides.pop("phone", f"555000{index:04d}"[:10]),
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
            external_id=overrides.pop("external_id", str(100 + index)),
            oauth_id=overrides.pop("oauth_id", f"oauth-{index}"),
            **overrides,
        )
        db.session.add(user)
        db.session.commit()
        user.plaintext_password = password
        return user

    return factory


@pytest.fixture
def day_factory(app):
    def factory(date=None, name=None, **overrides):
        date = date or datetime(2026, 3, 10).date()
        day = Day(name=name or date.strftime("%m/%d/%Y"), date=date, **overrides)
        db.session.add(day)
        db.session.commit()
        return day

    return factory


@pytest.fixture
def shift_factory(app, day_factory):
    def factory(day=None, start_time=None, **overrides):
        day = day or day_factory()
        start_time = start_time or datetime.combine(day.date, datetime.min.time()).replace(hour=9)
        shift = Shift(
            name=overrides.pop("name", "Test Shift"),
            startTime=start_time,
            duration=overrides.pop("duration", 400),
            maxEmployees=overrides.pop("maxEmployees", 3),
            minEmployees=overrides.pop("minEmployees", 1),
            day_id=overrides.pop("day_id", day.id),
            **overrides,
        )
        db.session.add(shift)
        db.session.commit()
        return shift

    return factory


@pytest.fixture
def assignment_factory(app):
    def factory(user, shift, **overrides):
        assignment = Assignment(user=user, shift=shift, **overrides)
        db.session.add(assignment)
        db.session.commit()
        return assignment

    return factory


@pytest.fixture
def alert_factory(app):
    def factory(user, **overrides):
        alert = Alert(
            recipient_user_id=user.id,
            content=overrides.pop(
                "content",
                {"title": "Test Alert", "message": "Notification body"},
            ),
            **overrides,
        )
        db.session.add(alert)
        db.session.commit()
        return alert

    return factory


@pytest.fixture
def feature_factory(app):
    def factory(name, enabled=False, **overrides):
        feature = Feature.query.filter_by(name=name).first()
        if feature is None:
            feature = Feature(name=name, enabled=enabled, **overrides)
            db.session.add(feature)
        else:
            feature.enabled = enabled
            for key, value in overrides.items():
                setattr(feature, key, value)
        db.session.commit()
        return feature

    return factory


@pytest.fixture
def log_field_factory(app):
    def factory(**overrides):
        index = LogField.query.count() + 1
        field = LogField(
            label=overrides.pop("label", f"Field {index}"),
            field_key=overrides.pop("field_key", f"field_{index}"),
            field_type=overrides.pop("field_type", "text"),
            required=overrides.pop("required", False),
            options=overrides.pop("options", []),
            position=overrides.pop("position", index),
            **overrides,
        )
        db.session.add(field)
        db.session.commit()
        return field

    return factory


@pytest.fixture
def log_entry_factory(app):
    def factory(user, **overrides):
        entry = LogEntry(
            user_id=user.id,
            related_shift_id=overrides.pop("related_shift_id", None),
            field_data=overrides.pop("field_data", {"note": "Test entry"}),
            **overrides,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    return factory


@pytest.fixture
def logged_in_user(user_factory, login_user):
    user = user_factory()
    login_user(user)
    return user


@pytest.fixture
def second_user(user_factory):
    return user_factory(email="other@test.com", external_id="222", oauth_id="oauth-other")


@pytest.fixture
def admin_user(user_factory, login_user):
    user = user_factory(
        email="admin@test.com",
        external_id="999",
        oauth_id="oauth-admin",
        meta={"is_admin": True},
    )
    login_user(user)
    return user
