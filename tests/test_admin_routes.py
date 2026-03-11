from datetime import datetime

from skedule import db
from skedule.models import Day, Feature, LogEntry, LogField, Shift


def test_configure_schedule_can_create_week(client, logged_in_user):
    response = client.post(
        "/schedule/configure?week=2026-03-09",
        data={"submitNewWeek": "Create Schedule"},
        follow_redirects=True,
    )

    created_days = Day.query.order_by(Day.date.asc()).all()
    assert response.status_code == 200
    assert b"Schedule created for the week of March 09, 2026" in response.data
    assert len(created_days) == 7
    assert created_days[0].date.isoformat() == "2026-03-09"
    assert created_days[-1].date.isoformat() == "2026-03-15"


def test_configure_schedule_can_delete_week(client, logged_in_user, day_factory, shift_factory):
    base_date = datetime(2026, 3, 9).date()
    days = [day_factory(date=base_date.replace(day=9 + offset)) for offset in range(7)]
    for index, day in enumerate(days):
        shift_factory(
            day=day,
            name=f"Shift {index}",
            start_time=datetime.combine(day.date, datetime.min.time()).replace(hour=8),
        )

    response = client.post(
        "/schedule/configure?week=2026-03-09",
        data={"submitDeleteWeek": "Delete Schedule"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Schedule deleted for the week of March 09, 2026" in response.data
    assert Day.query.count() == 0
    assert Shift.query.count() == 0


def test_add_shift_creates_shift_for_existing_day(client, logged_in_user, day_factory):
    day_factory(date=datetime(2026, 3, 9).date())

    response = client.post(
        "/schedule/configure/add-shift?datetime=2026-03-09-0900",
        data={
            "shiftName": "Morning Patrol",
            "startTime": "0930",
            "duration": "0400",
            "maxEmployees": 4,
            "minEmployees": 2,
            "employees": "",
            "submit": "Add Shift",
        },
        follow_redirects=True,
    )

    shift = Shift.query.filter_by(name="Morning Patrol").first()
    assert response.status_code == 200
    assert b"Shift Added!" in response.data
    assert shift is not None
    assert shift.startTime.strftime("%Y-%m-%d-%H%M") == "2026-03-09-0930"


def test_add_shift_invalid_datetime_returns_404(client, logged_in_user):
    response = client.get("/schedule/configure/add-shift?datetime=bad-value")

    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_manage_features_page_renders(client, logged_in_user):
    response = client.get("/admin/features")

    assert response.status_code == 200
    assert b"Features" in response.data
    assert b"/features/log" in response.data


def test_feature_api_rejects_missing_csrf_token(client, logged_in_user):
    response = client.post(
        "/api/admin/features/logs",
        json={"enabled": True},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Invalid CSRF token."


def test_feature_api_updates_enabled_features(client, logged_in_user):
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    response = client.post(
        "/api/admin/features/logs",
        json={"enabled": True},
        headers={"X-Feature-CSRF-Token": token},
    )

    logs_feature = Feature.query.filter_by(name="logs").first()
    assert response.status_code == 200
    assert response.get_json()["feature"]["enabled"] is True
    assert logs_feature is not None
    assert logs_feature.enabled is True


def test_log_settings_api_updates_settings_with_dependency(client, logged_in_user):
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    response = client.post(
        "/api/admin/features/log/settings",
        json={"require_current_shift": True},
        headers={"X-Feature-CSRF-Token": token},
    )

    logs_feature = Feature.query.filter_by(name="logs").first()
    assert response.status_code == 200
    assert response.get_json()["config"]["require_current_shift"] is True
    assert response.get_json()["config"]["require_relating_shift"] is True
    assert logs_feature.config["require_current_shift"] is True
    assert logs_feature.config["require_relating_shift"] is True


def test_log_settings_api_disabling_relating_shift_turns_off_current_shift(
    client,
    logged_in_user,
):
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    client.post(
        "/api/admin/features/log/settings",
        json={"require_current_shift": True},
        headers={"X-Feature-CSRF-Token": token},
    )
    response = client.post(
        "/api/admin/features/log/settings",
        json={"require_relating_shift": False},
        headers={"X-Feature-CSRF-Token": token},
    )

    assert response.status_code == 200
    assert response.get_json()["config"]["require_relating_shift"] is False
    assert response.get_json()["config"]["require_current_shift"] is False


def test_log_builder_page_renders(client, logged_in_user):
    response = client.get("/features/log")

    assert response.status_code == 200
    assert b"Log Builder" in response.data
    assert b'for="feature-logs"' in response.data
    assert b"Require relating shift" in response.data
    assert b"Require current shift" in response.data


def test_feature_detail_page_renders_for_simple_feature(client, logged_in_user):
    response = client.get("/features/leaderboard")

    assert response.status_code == 200
    assert b"Leaderboard" in response.data
    assert b"Detailed configuration for leaderboard is not implemented yet." in response.data


def test_log_builder_can_create_field(client, logged_in_user):
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    response = client.post(
        "/features/log",
        data={
            "feature_api_token": token,
            "label": "Start Time",
            "field_key": "start_time",
            "field_type": "time",
            "required": "on",
            "options": "",
        },
        follow_redirects=True,
    )

    field = LogField.query.filter_by(field_key="start_time").first()
    assert response.status_code == 200
    assert b"Log field added." in response.data
    assert field is not None
    assert field.field_type == "time"
    assert field.required is True


def test_log_builder_can_delete_field(client, logged_in_user, log_field_factory):
    field = log_field_factory(label="Unit", field_key="unit", field_type="text")
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    response = client.post(
        f"/features/log/field/{field.id}/delete",
        data={"feature_api_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Log field deleted." in response.data
    assert LogField.query.filter_by(id=field.id).first() is None


def test_log_builder_delete_api_removes_field(client, logged_in_user, log_field_factory):
    field = log_field_factory(label="Unit", field_key="unit_api", field_type="text")
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    response = client.delete(
        f"/api/admin/features/log/field/{field.id}",
        headers={"X-Feature-CSRF-Token": token},
    )

    assert response.status_code == 200
    assert response.get_json()["deleted_id"] == field.id
    assert LogField.query.filter_by(id=field.id).first() is None


def test_log_builder_can_reorder_fields(client, logged_in_user, log_field_factory):
    first = log_field_factory(label="First", field_key="first", position=1)
    second = log_field_factory(label="Second", field_key="second", position=2)
    client.get("/admin/features")
    with client.session_transaction() as session:
        token = session["feature_api_token"]

    response = client.post(
        "/api/admin/features/log/fields/reorder",
        json={"field_ids": [second.id, first.id]},
        headers={"X-Feature-CSRF-Token": token},
    )

    db.session.refresh(first)
    db.session.refresh(second)
    assert response.status_code == 200
    assert response.get_json()["field_ids"] == [second.id, first.id]
    assert first.position == 2
    assert second.position == 1


def test_view_logs_requires_feature_to_be_enabled(client, logged_in_user):
    response = client.get("/admin/logs")

    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_view_logs_renders_when_feature_is_enabled(client, logged_in_user, feature_factory):
    feature_factory(name="logs", enabled=True)

    response = client.get("/admin/logs")

    assert response.status_code == 200
    assert b"View Logs" in response.data


def test_view_logs_lists_submitted_entries(
    client,
    logged_in_user,
    feature_factory,
    log_entry_factory,
    shift_factory,
):
    feature_factory(name="logs", enabled=True)
    shift = shift_factory(name="Patrol Shift")
    log_entry_factory(
        user=logged_in_user,
        related_shift_id=shift.id,
        field_data={"officer": "Unit 12", "status": "Complete"},
    )

    response = client.get("/admin/logs")

    assert response.status_code == 200
    assert b"Patrol Shift" in response.data
    assert f"/schedule/shift/{shift.id}".encode() in response.data
    assert f"/log/{LogEntry.query.one().id}".encode() in response.data
