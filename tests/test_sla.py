from datetime import date, datetime, timezone

from app.reports.common.sla import (
    BusinessHoursConfig,
    business_hours_between,
    compute_sla_status,
    working_days_between,
)

NISSAN_HOURS = BusinessHoursConfig(is_24x7=False)  # Mon-Fri, 09:00-17:00 placeholder
KTC_HOURS = BusinessHoursConfig(is_24x7=True)


def dt(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


def test_business_hours_same_day_within_window():
    start = dt(2026, 7, 6, 10, 0)  # Monday
    end = dt(2026, 7, 6, 12, 0)
    assert business_hours_between(start, end, NISSAN_HOURS) == 2.0


def test_business_hours_clips_to_window():
    start = dt(2026, 7, 6, 16, 0)  # Monday 4pm
    end = dt(2026, 7, 6, 19, 0)  # 7pm, past 17:00 close
    assert business_hours_between(start, end, NISSAN_HOURS) == 1.0


def test_business_hours_skips_weekend():
    start = dt(2026, 7, 3, 16, 0)  # Friday 4pm
    end = dt(2026, 7, 6, 10, 0)  # Monday 10am
    # Fri 16:00-17:00 (1h) + Mon 09:00-10:00 (1h), Sat/Sun excluded
    assert business_hours_between(start, end, NISSAN_HOURS) == 2.0


def test_business_hours_24x7_is_wall_clock():
    start = dt(2026, 7, 3, 16, 0)
    end = dt(2026, 7, 6, 10, 0)
    assert business_hours_between(start, end, KTC_HOURS) == 66.0


def test_working_days_between_excludes_creation_day():
    start = date(2026, 7, 6)  # Monday
    end = date(2026, 7, 6)
    assert working_days_between(start, end) == 0


def test_working_days_between_skips_weekend():
    start = date(2026, 7, 3)  # Friday
    end = date(2026, 7, 6)  # Monday
    assert working_days_between(start, end) == 1  # only Monday counts


def test_compute_sla_status_met():
    result = compute_sla_status(
        priority="Highest",
        category=None,
        created=dt(2026, 7, 6, 9, 0),
        resolved=dt(2026, 7, 6, 11, 0),
        config=NISSAN_HOURS,
    )
    assert result.level == "L1"
    assert result.met is True


def test_compute_sla_status_unresolved_is_none():
    result = compute_sla_status(
        priority="High",
        category=None,
        created=dt(2026, 7, 6, 9, 0),
        resolved=None,
        config=NISSAN_HOURS,
    )
    assert result.met is None


def test_compute_sla_status_inquiry_uses_working_days():
    result = compute_sla_status(
        priority="Medium",
        category="Inquiry",
        created=dt(2026, 7, 3, 9, 0),  # Friday
        resolved=dt(2026, 7, 6, 9, 0),  # Monday
        config=NISSAN_HOURS,
    )
    assert result.unit == "working_days"
    assert result.target == 2
