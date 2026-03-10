from tests.frontend.conftest import parse_html


def test_template_listing_page_renders_existing_templates(client, logged_in_user):
    response = client.get("/schedule/configure/templates")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.find("h1", string=lambda text: text and "Template Manager" in text) is not None
    assert soup.select_one("table.table") is not None
    assert any("Create" in link.get_text(" ", strip=True) for link in soup.find_all("a"))
