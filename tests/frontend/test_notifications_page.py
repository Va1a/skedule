from tests.frontend.conftest import parse_html


def test_notifications_page_renders_alert_card_and_dismiss_modal(client, logged_in_user, alert_factory):
    alert_factory(
        user=logged_in_user,
        seen=False,
        content={"title": "Assignment Updated", "message": "Shift changed"},
    )

    response = client.get("/alerts")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "Notifications"
    assert any("Assignment Updated" in heading.get_text(" ", strip=True) for heading in soup.find_all("h6"))
    assert any("Shift changed" in paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p"))
    assert soup.select_one("div#dismissModal") is not None
    assert soup.select_one("form#dismissForm") is not None
