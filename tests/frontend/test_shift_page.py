from datetime import datetime

from tests.frontend.conftest import parse_html


def test_shift_details_page_renders_request_controls(client, logged_in_user, shift_factory):
    shift = shift_factory(name="Evening Shift", start_time=datetime(2026, 3, 10, 17, 0))

    response = client.get(f"/schedule/shift/{shift.id}")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "Shift Details"
    assert soup.select_one("input#shiftName[value='Evening Shift']") is not None
    assert soup.find("button", string=lambda text: text and "Request Shift" in text) is not None
    assert soup.find("li", string=lambda text: text and "No Employees" in text) is not None
