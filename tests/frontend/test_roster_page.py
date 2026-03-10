from tests.frontend.conftest import parse_html


def test_roster_page_renders_user_table(client, logged_in_user, second_user):
    response = client.get("/roster")
    soup = parse_html(response)

    rows = soup.select("tbody#rosterTable tr")
    headers = [header.get_text(strip=True) for header in soup.select("table thead th")]

    assert response.status_code == 200
    assert soup.find("h1", string="Roster") is not None
    assert headers == ["Employee #", "Name", "Email", "Phone Number", "Edit"]
    assert len(rows) >= 2
    assert any(second_user.email in row.get_text(" ", strip=True) for row in rows)
