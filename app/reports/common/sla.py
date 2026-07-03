"""SLA math: priority -> level mapping, elapsed-time calculators, and the
per-issue SLA verdict. Kept pure and independent of Jira/output format so it
can be unit tested in isolation (tests/test_sla.py) — business-hours math is
the easiest place to introduce a subtle off-by-one bug.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional


@dataclass(frozen=True)
class BusinessHoursConfig:
    """Support-hours window for a given client. Nissan/MEA/MTS are 8x5
    (Mon-Fri, a fixed daily window); KTC is 24x7. Confirm exact clock hours
    with the client before relying on this for real SLA reporting — 09:00-
    17:00 below is a placeholder (plan Open Item #3)."""

    is_24x7: bool = False
    day_start: time = time(9, 0)
    day_end: time = time(17, 0)
    open_weekdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})  # Mon-Fri


# L1/L2/L3 targets are in business hours; Inquiry/Service Request targets are
# in working days. Confirm exact priority-name -> level mapping against the
# Nissan Jira project before going live (plan Open Item #1) — these are
# Jira's *default* priority names used only as a documented placeholder.
PRIORITY_TO_LEVEL = {
    "Highest": "L1",
    "High": "L2",
    "Medium": "L3",
}

LEVEL_TARGET_HOURS = {
    "L1": 4,
    "L2": 6,
    "L3": 8,
}

CATEGORY_TARGET_DAYS = {
    "Inquiry": 2,
    "Service Request": 3,
}


def business_hours_between(start: datetime, end: datetime, config: BusinessHoursConfig) -> float:
    """Elapsed support hours between start and end, clipped to the
    client's business-hours window and open weekdays. Returns wall-clock
    hours unchanged for 24x7 clients."""
    if end <= start:
        return 0.0
    if config.is_24x7:
        return (end - start).total_seconds() / 3600

    total = timedelta()
    day = start.date()
    while day <= end.date():
        if day.weekday() in config.open_weekdays:
            window_start = datetime.combine(day, config.day_start, tzinfo=start.tzinfo)
            window_end = datetime.combine(day, config.day_end, tzinfo=start.tzinfo)
            overlap_start = max(window_start, start)
            overlap_end = min(window_end, end)
            if overlap_end > overlap_start:
                total += overlap_end - overlap_start
        day += timedelta(days=1)
    return total.total_seconds() / 3600


def working_days_between(start: date, end: date, open_weekdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})) -> int:
    """Count of working days strictly between start and end, not counting
    the creation day itself (day 0 = creation day, per plan Open Item #3 —
    confirm this convention against a real historical example before
    shipping)."""
    if end <= start:
        return 0
    count = 0
    day = start + timedelta(days=1)
    while day <= end:
        if day.weekday() in open_weekdays:
            count += 1
        day += timedelta(days=1)
    return count


@dataclass
class SLAResult:
    level: Optional[str]
    target: Optional[float]
    actual: Optional[float]
    unit: str  # "business_hours" or "working_days"
    met: Optional[bool]


def compute_sla_status(
    priority: Optional[str],
    category: Optional[str],
    created: Optional[datetime],
    resolved: Optional[datetime],
    config: BusinessHoursConfig,
) -> SLAResult:
    """Looks up the right target (failure-recovery level, or inquiry/service-
    request day count) and computes actual vs target. Unresolved issues get
    met=None (can't evaluate yet) rather than being counted as a breach."""
    if category in CATEGORY_TARGET_DAYS:
        target = CATEGORY_TARGET_DAYS[category]
        if resolved is None or created is None:
            return SLAResult(level=None, target=target, actual=None, unit="working_days", met=None)
        actual = working_days_between(created.date(), resolved.date())
        return SLAResult(level=None, target=target, actual=actual, unit="working_days", met=actual <= target)

    level = PRIORITY_TO_LEVEL.get(priority)
    if level is None:
        return SLAResult(level=None, target=None, actual=None, unit="business_hours", met=None)
    target = LEVEL_TARGET_HOURS[level]
    if resolved is None or created is None:
        return SLAResult(level=level, target=target, actual=None, unit="business_hours", met=None)
    actual = business_hours_between(created, resolved, config)
    return SLAResult(level=level, target=target, actual=actual, unit="business_hours", met=actual <= target)
