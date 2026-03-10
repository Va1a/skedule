from datetime import datetime

from skedule.models import Day, Shift


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
