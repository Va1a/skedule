from tests.frontend.conftest import parse_html


def test_log_detail_page_renders_field_responses(
    client,
    logged_in_user,
    feature_factory,
    log_entry_factory,
    log_field_factory,
    shift_factory,
):
    feature_factory(name="logs", enabled=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text")
    shift = shift_factory(name="Test")
    entry = log_entry_factory(
        user=logged_in_user,
        related_shift_id=shift.id,
        field_data={"officer": "Unit 12"},
    )

    response = client.get(f"/log/{entry.id}")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "Log Entry"
    assert soup.select_one(f"a[href='/schedule/shift/{shift.id}']").get_text(strip=True) == "Test"
    assert "Officer" in soup.get_text(" ", strip=True)
    assert "Unit 12" in soup.get_text(" ", strip=True)
