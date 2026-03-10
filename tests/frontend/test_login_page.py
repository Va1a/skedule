from tests.frontend.conftest import parse_html


def test_login_page_renders_expected_form(client):
    response = client.get("/login")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.title.string.strip() == "Skedule - Login"
    assert soup.select_one("form#loginForm") is not None
    assert soup.select_one("input#emailInput[name='email']") is not None
    assert soup.select_one("input#passwordInput[name='password']") is not None
    assert soup.select_one("input#rememberCheck[name='remember']") is not None
    assert soup.select_one("input#loginButton[value='Log In']") is not None
