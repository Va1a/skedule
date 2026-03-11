from datetime import datetime

from skedule import db
from skedule.models import Alert, Assignment


def test_home_requires_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login?next=%2F" in response.headers["Location"]


def test_request_shift_creates_pending_assignment(client, logged_in_user, shift_factory):
    shift = shift_factory()

    response = client.post(
        f"/schedule/shift/{shift.id}/request",
        follow_redirects=True,
    )

    assignment = Assignment.query.filter_by(user_id=logged_in_user.id, shift_id=shift.id).first()
    assert response.status_code == 200
    assert b"Shift request submitted." in response.data
    assert assignment is not None
    assert assignment.request is True
    assert assignment.confirmed is True


def test_request_shift_rejects_duplicate_assignment(client, logged_in_user, shift_factory, assignment_factory):
    shift = shift_factory()
    assignment_factory(user=logged_in_user, shift=shift, request=False, confirmed=True)

    response = client.post(
        f"/schedule/shift/{shift.id}/request",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"You already have a request/assignment for this shift." in response.data
    assert Assignment.query.filter_by(user_id=logged_in_user.id, shift_id=shift.id).count() == 1


def test_remove_shift_request_deletes_assignment(client, logged_in_user, shift_factory, assignment_factory):
    shift = shift_factory()
    assignment = assignment_factory(user=logged_in_user, shift=shift, request=True, confirmed=True)

    response = client.post(
        f"/schedule/shift/{shift.id}/remove-request",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Shift request removed." in response.data
    assert db.session.get(Assignment, assignment.id) is None


def test_remove_shift_request_handles_missing_assignment(client, logged_in_user, shift_factory):
    shift = shift_factory()

    response = client.post(
        f"/schedule/shift/{shift.id}/remove-request",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"You do not have a pending request for this shift." in response.data


def test_schedule_invalid_week_returns_404(client, logged_in_user):
    response = client.get("/schedule?week=not-a-date")

    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_log_page_requires_feature_to_be_enabled(client, logged_in_user):
    response = client.get("/log")

    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_log_page_renders_when_feature_is_enabled(client, logged_in_user, feature_factory):
    feature_factory(name="logs", enabled=True)

    response = client.get("/log")

    assert response.status_code == 200
    assert b"Log" in response.data


def test_log_page_renders_dynamic_fields_when_configured(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
):
    feature_factory(name="logs", enabled=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text", required=True)
    log_field_factory(label="Start Time", field_key="start_time", field_type="time")
    log_field_factory(
        label="Shift Type",
        field_key="shift_type",
        field_type="select",
        options=["Patrol", "Desk"],
    )

    response = client.get("/log")

    assert response.status_code == 200
    assert b'name="officer"' in response.data
    assert b'type="time"' in response.data
    assert b'<option value="Patrol">Patrol</option>' in response.data


def test_leaderboard_requires_feature_to_be_enabled(client, logged_in_user):
    response = client.get("/leaderboard")

    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_leaderboard_renders_when_feature_is_enabled(client, logged_in_user, feature_factory):
    feature_factory(name="leaderboard", enabled=True)

    response = client.get("/leaderboard")

    assert response.status_code == 200
    assert b"Leaderboard" in response.data


def test_discussion_requires_feature_to_be_enabled(client, logged_in_user):
    response = client.get("/discussion")

    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_discussion_renders_when_feature_is_enabled(client, logged_in_user, feature_factory):
    feature_factory(name="discussion", enabled=True)

    response = client.get("/discussion")

    assert response.status_code == 200
    assert b"Discussion" in response.data


def test_upcoming_can_hide_pending_requests(
    client,
    logged_in_user,
    day_factory,
    shift_factory,
    assignment_factory,
):
    future_day = day_factory(date=datetime(2026, 3, 15).date())
    confirmed_shift = shift_factory(day=future_day, name="Confirmed Shift")
    pending_shift = shift_factory(
        day=future_day,
        name="Pending Shift",
        start_time=datetime(2026, 3, 15, 13, 0),
    )
    assignment_factory(user=logged_in_user, shift=confirmed_shift, request=False, confirmed=True)
    assignment_factory(user=logged_in_user, shift=pending_shift, request=True, confirmed=True)

    response = client.get("/upcoming?no-pending=true")

    assert response.status_code == 200
    assert b"Confirmed Shift" in response.data
    assert b"Pending Shift" not in response.data
    assert b"does not include your pending shift requests" in response.data


def test_pending_requests_only_lists_requested_assignments(
    client,
    logged_in_user,
    day_factory,
    shift_factory,
    assignment_factory,
):
    future_day = day_factory(date=datetime(2026, 3, 16).date())
    requested_shift = shift_factory(day=future_day, name="Requested Shift")
    confirmed_shift = shift_factory(
        day=future_day,
        name="Confirmed Shift",
        start_time=datetime(2026, 3, 16, 13, 0),
    )
    assignment_factory(user=logged_in_user, shift=requested_shift, request=True, confirmed=True)
    assignment_factory(user=logged_in_user, shift=confirmed_shift, request=False, confirmed=True)

    response = client.get("/pending-requests")

    assert response.status_code == 200
    assert b"Requested Shift" in response.data
    assert b"Confirmed Shift" not in response.data


def test_notifications_marks_visible_alerts_seen(client, logged_in_user, alert_factory):
    first_alert = alert_factory(user=logged_in_user, seen=False, content={"title": "First", "message": "Body 1"})
    second_alert = alert_factory(user=logged_in_user, seen=False, content={"title": "Second", "message": "Body 2"})

    response = client.get("/alerts")

    db_alerts = Alert.query.filter(Alert.id.in_([first_alert.id, second_alert.id])).all()
    assert response.status_code == 200
    assert b"First" in response.data
    assert b"Second" in response.data
    assert all(alert.seen is True for alert in db_alerts)


def test_dismiss_alert_rejects_other_users_alert(client, logged_in_user, second_user, alert_factory):
    other_alert = alert_factory(user=second_user)

    response = client.post(f"/alerts/{other_alert.id}/dismiss")

    assert response.status_code == 403
    assert db.session.get(Alert, other_alert.id) is not None
    assert b"403 - Forbidden" in response.data


def test_dismiss_alert_deletes_current_users_alert(client, logged_in_user, alert_factory):
    alert = alert_factory(user=logged_in_user)

    response = client.post(f"/alerts/{alert.id}/dismiss", follow_redirects=True)

    assert response.status_code == 200
    assert b"Alert dismissed." in response.data
    assert db.session.get(Alert, alert.id) is None
