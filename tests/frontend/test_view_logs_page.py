from tests.frontend.conftest import parse_html


def test_view_logs_page_renders_submitted_log_entries(
    client,
    logged_in_user,
    feature_factory,
    log_entry_factory,
    shift_factory,
):
    feature_factory(name="logs", enabled=True)
    shift = shift_factory(name="Patrol Shift")
    entry = log_entry_factory(
        user=logged_in_user,
        related_shift_id=shift.id,
        field_data={"officer": "Unit 12"},
    )

    response = client.get("/admin/logs")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "View Logs"
    assert soup.select_one(f"a[href='/schedule/shift/{shift.id}']").get_text(strip=True) == "Patrol Shift"
    assert soup.select_one(f"a[href='/log/{entry.id}']").get_text(strip=True) == "Open"
