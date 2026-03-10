from datetime import datetime

from tests.frontend.conftest import parse_html


def test_configure_schedule_page_renders_create_modal_when_week_missing(client, logged_in_user):
    response = client.get("/schedule/configure?week=2026-03-09")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("div#createWeekModal") is not None
    assert soup.select_one("button[data-bs-target='#createWeekModal']") is not None
    assert soup.find(string=lambda text: text and "A schedule for this week has not yet been created." in text) is not None


def test_configure_schedule_page_renders_delete_modal_and_shift_links_for_existing_week(
    client,
    logged_in_user,
    day_factory,
    shift_factory,
):
    week_start = datetime(2026, 3, 9).date()
    days = [day_factory(date=week_start.replace(day=week_start.day + offset)) for offset in range(7)]
    shift = shift_factory(day=days[0], name="Operations", start_time=datetime(2026, 3, 9, 9, 0))

    response = client.get("/schedule/configure?week=2026-03-09")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("div#deleteWeekModal") is not None
    assert any(link.get_text(" ", strip=True) == "Operations" for link in soup.find_all("a"))
    assert soup.select_one(f"a[href='/schedule/configure/shift/{shift.id}']") is not None
