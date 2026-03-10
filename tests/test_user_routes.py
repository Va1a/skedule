from skedule.models import User


def test_register_creates_user_and_hashes_password(client):
    response = client.post(
        "/register",
        data={
            "name": "New User",
            "email": "new@test.com",
            "phone": "1234567890",
            "password": "secret123",
            "confirm": "secret123",
            "submit": "Register",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Account created, you may now log in." in response.data

    user = User.query.filter_by(email="new@test.com").first()
    assert user is not None
    assert user.password != "secret123"


def test_register_rejects_duplicate_email(client, user_factory):
    user_factory(email="dupe@test.com")

    response = client.post(
        "/register",
        data={
            "name": "Another User",
            "email": "dupe@test.com",
            "phone": "1234567890",
            "password": "secret123",
            "confirm": "secret123",
            "submit": "Register",
        },
    )

    assert response.status_code == 200
    assert b"already been registered" in response.data
    assert User.query.filter_by(email="dupe@test.com").count() == 1


def test_login_redirects_to_home_and_logout_clears_session(client, user_factory):
    user = user_factory(email="login@test.com", password="secret123")

    login_response = client.post(
        "/login",
        data={
            "email": user.email,
            "password": "secret123",
            "submit": "Log In",
        },
        follow_redirects=True,
    )

    assert login_response.status_code == 200
    assert b"Dashboard" in login_response.data
    assert b"Logged in as" in login_response.data

    logout_response = client.get("/logout", follow_redirects=True)

    assert logout_response.status_code == 200
    assert b"You have been logged out." in logout_response.data
    assert b"Please sign in to your account." in logout_response.data


def test_login_with_invalid_credentials_shows_error(client, user_factory):
    user_factory(email="wrong@test.com", password="correct-password")

    response = client.post(
        "/login",
        data={
            "email": "wrong@test.com",
            "password": "bad-password",
            "submit": "Log In",
        },
    )

    assert response.status_code == 200
    assert b"Invalid credentials." in response.data
