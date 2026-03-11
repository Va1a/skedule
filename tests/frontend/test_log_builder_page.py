from tests.frontend.conftest import parse_html


def test_log_builder_page_renders_toggle_add_form_and_field_table(client, logged_in_user):
    response = client.get("/features/log")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "Log Builder"
    assert soup.select_one(".border-bottom .feature-page-switch input#feature-logs.feature-toggle") is not None
    assert soup.select_one("input#require-relating-shift.log-setting-toggle") is not None
    assert soup.select_one("input#require-current-shift.log-setting-toggle") is not None
    assert soup.select_one("form input#label") is not None
    assert soup.select_one("form input#field_key") is not None
    assert soup.select_one("form select#field_type") is not None
    assert any(
        heading.get_text(strip=True) == "Current Fields"
        for heading in soup.find_all(["h2", "h3"])
    )


def test_log_builder_page_renders_drag_handle_for_existing_fields(
    client,
    logged_in_user,
    log_field_factory,
):
    log_field_factory(label="Officer", field_key="officer")

    response = client.get("/features/log")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("#logFieldsTableBody tr[draggable='true']") is not None
    assert soup.select_one(".log-drag-handle") is not None
    assert soup.select_one(".log-delete-button[data-field-id]") is not None
