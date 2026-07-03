from datetime import date

from app.jira import queries as Q
from app.jira.models import ScopeParams

SCOPE = ScopeParams(start_date=date(2026, 5, 1), end_date=date(2026, 5, 31), project_key="NISS")


def test_jql_current_period_filters_by_created():
    jql = Q.jql_current_period(SCOPE)
    assert 'project = "NISS"' in jql
    assert 'created >= "2026-05-01"' in jql
    assert 'created <= "2026-05-31"' in jql


def test_jql_carry_over_closed_spans_boundary():
    jql = Q.jql_carry_over_closed(SCOPE)
    assert 'created < "2026-05-01"' in jql
    assert 'resolutiondate >= "2026-05-01"' in jql
    assert 'resolutiondate <= "2026-05-31"' in jql


def test_jql_carry_over_open_is_unresolved_at_period_end():
    jql = Q.jql_carry_over_open(SCOPE)
    assert 'created <= "2026-05-31"' in jql
    assert "resolution = Unresolved" in jql


def test_jql_open_at_period_start():
    jql = Q.jql_open_at_period_start(SCOPE)
    assert 'created < "2026-05-01"' in jql
    assert "resolutiondate is EMPTY" in jql
    assert 'resolutiondate >= "2026-05-01"' in jql


def test_jql_closed_during_period_ignores_created_date():
    jql = Q.jql_closed_during_period(SCOPE)
    assert "created" not in jql.replace('project = "NISS"', "")
    assert 'resolutiondate >= "2026-05-01"' in jql


def test_jql_fiscal_year_trend_spans_april_to_march():
    jql = Q.jql_fiscal_year_trend("NISS", date(2026, 5, 31))
    assert 'created >= "2026-04-01"' in jql
    assert 'created <= "2027-03-31"' in jql
