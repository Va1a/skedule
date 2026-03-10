from datetime import datetime

from skedule.utils import daysOfCalendarWeek, getDayName, oneWeekLater, oneWeekPrior, ymdToDateTime, ymdhmToDateTime


def test_ymd_to_datetime_parses_valid_dates_and_rejects_invalid_input():
    assert ymdToDateTime("2026-03-10") == datetime(2026, 3, 10)
    assert ymdToDateTime("03/10/2026") is None
    assert ymdToDateTime(None) is None


def test_ymdhm_to_datetime_parses_valid_datetimes_and_rejects_invalid_input():
    assert ymdhmToDateTime("2026-03-10-0930") == datetime(2026, 3, 10, 9, 30)
    assert ymdhmToDateTime("2026-03-10 09:30") is None
    assert ymdhmToDateTime(None) is None


def test_days_of_calendar_week_returns_monday_through_sunday():
    week = daysOfCalendarWeek(datetime(2026, 3, 12, 15, 30))

    assert [day.date().isoformat() for day in week] == [
        "2026-03-09",
        "2026-03-10",
        "2026-03-11",
        "2026-03-12",
        "2026-03-13",
        "2026-03-14",
        "2026-03-15",
    ]


def test_one_week_helpers_offset_by_seven_days():
    base = datetime(2026, 3, 10, 9, 0)

    assert oneWeekPrior(base) == datetime(2026, 3, 3, 9, 0)
    assert oneWeekLater(base) == datetime(2026, 3, 17, 9, 0)


def test_get_day_name_maps_weekday_numbers():
    assert getDayName(0) == "Monday"
    assert getDayName(6) == "Sunday"
