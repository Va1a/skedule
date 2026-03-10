from datetime import datetime

import pytest

from skedule import bcrypt, create_app, db
from skedule.models import Alert, Assignment, Day, Shift, User
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
def logged_in_user(client, user_factory):
    user = user_factory()
    response = client.post(
        "/login",
        data={
            "email": user.email,
            "password": user.plaintext_password,
            "submit": "Log In",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    return user


@pytest.fixture
def second_user(user_factory):
    return user_factory(email="other@test.com", external_id="222", oauth_id="oauth-other")
