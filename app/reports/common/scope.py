"""Fiscal-year helpers. The client's fiscal year runs April -> March, not
January -> December, so any month-ordering logic must go through here rather
than using date.month directly (see plan Key Risks)."""

from dataclasses import dataclass
from datetime import date, timedelta

FISCAL_YEAR_START_MONTH = 4  # April
FISCAL_MONTH_ORDER = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]


def fiscal_month_index(d: date) -> int:
    """0 = April, 11 = March."""
    return FISCAL_MONTH_ORDER.index(d.month)


def fiscal_year_label(d: date) -> str:
    """Nissan labels fiscal years as e.g. FY26 for Apr-2026..Mar-2027."""
    year = d.year if d.month >= FISCAL_YEAR_START_MONTH else d.year - 1
    return f"FY{str(year)[-2:]}"


@dataclass
class FiscalYearBounds:
    start: date
    end: date  # inclusive last day of fiscal year


def fiscal_year_bounds(d: date) -> FiscalYearBounds:
    year = d.year if d.month >= FISCAL_YEAR_START_MONTH else d.year - 1
    start = date(year, FISCAL_YEAR_START_MONTH, 1)
    end = date(year + 1, FISCAL_YEAR_START_MONTH, 1)
    return FiscalYearBounds(start=start, end=end - timedelta(days=1))
