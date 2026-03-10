from tests.frontend.conftest import parse_html


def test_register_page_renders_expected_form(client):
    response = client.get("/register")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.title.string.strip() == "Skedule - Register"
    assert soup.select_one("form#registerForm") is not None
    assert soup.select_one("input#nameInput[name='name']") is not None
    assert soup.select_one("input#emailInput[name='email']") is not None
    assert soup.select_one("input#phoneInput[name='phone']") is not None
    assert soup.select_one("input#passwordInput[name='password']") is not None
    assert soup.select_one("input#confirmInput[name='confirm']") is not None
    assert soup.select_one("input#registerButton[value='Register']") is not None
