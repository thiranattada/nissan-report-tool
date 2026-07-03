from datetime import date

from app.reports.common.scope import (
    fiscal_month_index,
    fiscal_year_bounds,
    fiscal_year_label,
)


def test_fiscal_month_index_april_is_zero():
    assert fiscal_month_index(date(2026, 4, 15)) == 0


def test_fiscal_month_index_march_is_eleven():
    assert fiscal_month_index(date(2027, 3, 1)) == 11


def test_fiscal_year_label_matches_sample_report():
    # sample report: "AMO Summary man-hour for FY26 (As of May 2026)"
    assert fiscal_year_label(date(2026, 5, 1)) == "FY26"


def test_fiscal_year_label_before_april_is_previous_fy():
    assert fiscal_year_label(date(2027, 3, 1)) == "FY26"


def test_fiscal_year_bounds():
    bounds = fiscal_year_bounds(date(2026, 5, 1))
    assert bounds.start == date(2026, 4, 1)
    assert bounds.end == date(2027, 3, 31)
