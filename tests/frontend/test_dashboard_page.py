from datetime import datetime

from tests.frontend.conftest import parse_html


def test_dashboard_renders_navigation_and_shift_summary(
    client,
    logged_in_user,
    day_factory,
    shift_factory,
    assignment_factory,
    alert_factory,
):
    day = day_factory(date=datetime(2026, 3, 10).date())
    shift = shift_factory(day=day, name="Morning Patrol", start_time=datetime(2026, 3, 10, 9, 0))
    assignment_factory(user=logged_in_user, shift=shift, request=False, confirmed=True)
    alert_factory(user=logged_in_user, seen=False, content={"title": "Unread", "message": "New alert"})

    response = client.get("/")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "Dashboard"
    assert soup.select_one("a.nav-link[href='/schedule']") is not None
    assert soup.select_one("a.nav-link[href='/log']") is None
    assert soup.select_one("a.nav-link[href='/leaderboard']") is None
    assert soup.select_one("a.nav-link[href='/discussion']") is None
    assert soup.select_one("a.nav-link[href='/alerts'] .badge") is not None
    assert any("Morning Patrol" in link.get_text(" ", strip=True) for link in soup.find_all("a"))
    assert soup.find(string=lambda text: text and "Quick Stats" in text) is not None


def test_dashboard_shows_log_navigation_when_logs_feature_enabled(
    client,
    logged_in_user,
    feature_factory,
):
    feature_factory(name="logs", enabled=True)

    response = client.get("/")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("a.nav-link[href='/log']") is not None
    assert soup.select_one("a.nav-link[href='/admin/logs']") is not None


def test_dashboard_shows_other_feature_links_when_enabled(
    client,
    logged_in_user,
    feature_factory,
):
    feature_factory(name="leaderboard", enabled=True)
    feature_factory(name="discussion", enabled=True)

    response = client.get("/")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("a.nav-link[href='/leaderboard']") is not None
    assert soup.select_one("a.nav-link[href='/discussion']") is not None
