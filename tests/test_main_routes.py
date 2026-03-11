from datetime import datetime, timedelta

from skedule import db
from skedule.models import Alert, Assignment, LogEntry
from skedule.utils import getLocalizedTime


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


def test_log_submission_creates_log_entry(client, logged_in_user, feature_factory, log_field_factory):
    feature_factory(name="logs", enabled=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text", required=True)

    response = client.post(
        "/log",
        data={"officer": "Unit 12"},
        follow_redirects=True,
    )

    entry = LogEntry.query.one()
    assert response.status_code == 200
    assert b"Log entry submitted." in response.data
    assert entry.user_id == logged_in_user.id
    assert entry.field_data["officer"] == "Unit 12"


def test_log_detail_page_renders_for_submitter(
    client,
    logged_in_user,
    feature_factory,
    log_entry_factory,
    shift_factory,
):
    feature_factory(name="logs", enabled=True)
    shift = shift_factory(name="Test")
    entry = log_entry_factory(
        user=logged_in_user,
        related_shift_id=shift.id,
        field_data={"officer": "Unit 12"},
    )

    response = client.get(f"/log/{entry.id}")

    assert response.status_code == 200
    assert b"Log Entry" in response.data
    assert b"Unit 12" in response.data
    assert f"/schedule/shift/{shift.id}".encode() in response.data


def test_log_detail_page_allows_admin_to_view_other_users_entry(
    client,
    admin_user,
    second_user,
    feature_factory,
    log_entry_factory,
):
    feature_factory(name="logs", enabled=True)
    entry = log_entry_factory(user=second_user, field_data={"officer": "Unit 99"})

    response = client.get(f"/log/{entry.id}")

    assert response.status_code == 200
    assert b"Unit 99" in response.data


def test_log_detail_page_rejects_non_admin_non_submitter(
    client,
    logged_in_user,
    second_user,
    feature_factory,
    log_entry_factory,
):
    feature_factory(name="logs", enabled=True)
    entry = log_entry_factory(user=second_user, field_data={"officer": "Unit 44"})

    response = client.get(f"/log/{entry.id}")

    assert response.status_code == 403


def test_log_submission_with_related_shift_records_selected_shift(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
    shift_factory,
    assignment_factory,
):
    feature_factory(
        name="logs",
        enabled=True,
        config={"require_relating_shift": True, "require_current_shift": False},
    )
    shift = shift_factory(name="Assigned Shift")
    assignment_factory(user=logged_in_user, shift=shift, request=False, confirmed=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text", required=True)

    response = client.post(
        "/log",
        data={"officer": "Unit 12", "related_shift_id": shift.id},
        follow_redirects=True,
    )

    entry = LogEntry.query.one()
    assert response.status_code == 200
    assert entry.related_shift_id == shift.id


def test_log_submission_with_current_shift_records_active_shift(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
    shift_factory,
    assignment_factory,
):
    feature_factory(
        name="logs",
        enabled=True,
        config={"require_relating_shift": True, "require_current_shift": True},
    )
    active_shift = shift_factory(
        name="Active Shift",
        start_time=getLocalizedTime().replace(tzinfo=None) - timedelta(minutes=30),
        duration=100,
    )
    assignment_factory(user=logged_in_user, shift=active_shift, request=False, confirmed=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text", required=True)

    response = client.post(
        "/log",
        data={"officer": "Unit 12"},
        follow_redirects=True,
    )

    entry = LogEntry.query.one()
    assert response.status_code == 200
    assert entry.related_shift_id == active_shift.id


def test_log_page_can_require_related_shift_selection(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
    shift_factory,
    assignment_factory,
):
    feature_factory(
        name="logs",
        enabled=True,
        config={"require_relating_shift": True, "require_current_shift": False},
    )
    shift = shift_factory(name="Assigned Shift")
    assignment_factory(user=logged_in_user, shift=shift, request=False, confirmed=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text")

    response = client.get("/log")

    assert response.status_code == 200
    assert b'name="related_shift_id"' in response.data
    assert b"Select one of your shifts" in response.data
    assert b"Assigned Shift" in response.data


def test_log_page_can_require_current_shift(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
    shift_factory,
    assignment_factory,
):
    feature_factory(
        name="logs",
        enabled=True,
        config={"require_relating_shift": True, "require_current_shift": True},
    )
    active_shift = shift_factory(
        name="Active Shift",
        start_time=getLocalizedTime().replace(tzinfo=None) - timedelta(minutes=30),
        duration=100,
    )
    assignment_factory(user=logged_in_user, shift=active_shift, request=False, confirmed=True)
    log_field_factory(label="Officer", field_key="officer", field_type="text")

    response = client.get("/log")

    assert response.status_code == 200
    assert b'name="related_shift_id"' in response.data
    assert b"This log will be associated with your current active shift." in response.data
    assert b"Active Shift" in response.data


def test_log_page_warns_when_current_shift_is_required_but_missing(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
):
    feature_factory(
        name="logs",
        enabled=True,
        config={"require_relating_shift": True, "require_current_shift": True},
    )
    log_field_factory(label="Officer", field_key="officer", field_type="text")

    response = client.get("/log")

    assert response.status_code == 200
    assert b"You must currently be within one of your assigned shifts to submit a log." in response.data


def test_log_page_limits_related_shift_picker_to_50_closest_shifts(
    client,
    logged_in_user,
    feature_factory,
    log_field_factory,
    day_factory,
    shift_factory,
    assignment_factory,
):
    feature_factory(
        name="logs",
        enabled=True,
        config={"require_relating_shift": True, "require_current_shift": False},
    )
    log_field_factory(label="Officer", field_key="officer", field_type="text")
    base_time = getLocalizedTime().replace(tzinfo=None)

    days_by_date = {}
    for index in range(55):
        shift_time = base_time + timedelta(hours=index - 27)
        day = days_by_date.get(shift_time.date())
        if day is None:
            day = day_factory(date=shift_time.date())
            days_by_date[shift_time.date()] = day
        shift = shift_factory(
            day=day,
            name=f"Shift {index}",
            start_time=shift_time,
        )
        assignment_factory(user=logged_in_user, shift=shift, request=False, confirmed=True)

    response = client.get("/log")

    assert response.status_code == 200
    assert response.data.count(b"<option value=") == 51
    assert b"Shift 27" in response.data
    assert b"Shift 0" not in response.data


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
