"""Pure JQL-string builders. No I/O here — see service.py for the calls that
actually hit Jira. Keeping these pure makes them unit-testable without a live
Jira connection (see tests/test_queries.py)."""

from datetime import date

from app.jira.models import ScopeParams
from app.reports.common.scope import fiscal_year_bounds


def _jql(project_key: str, *clauses: str) -> str:
    parts = [f'project = "{project_key}"', *clauses]
    return " AND ".join(parts)


def jql_current_period(scope: ScopeParams) -> str:
    """Issues created within the period, OR still open and touching it."""
    return _jql(
        scope.project_key,
        f'created >= "{scope.start_date}" AND created <= "{scope.end_date}"',
    )


def jql_carry_over_closed(scope: ScopeParams) -> str:
    """Opened before this period, resolved during this period."""
    return _jql(
        scope.project_key,
        f'created < "{scope.start_date}"',
        f'resolutiondate >= "{scope.start_date}" AND resolutiondate <= "{scope.end_date}"',
    )


def jql_carry_over_open(scope: ScopeParams) -> str:
    """Opened before or during this period, still unresolved as of period end
    (this is also next period's "open at period start" bucket)."""
    return _jql(
        scope.project_key,
        f'created <= "{scope.end_date}"',
        "resolution = Unresolved",
    )


def jql_open_at_period_start(scope: ScopeParams) -> str:
    """The "Carry over (A)" column of the incident summary table: issues
    opened before this period that were still unresolved as of period start."""
    return _jql(
        scope.project_key,
        f'created < "{scope.start_date}"',
        f'(resolutiondate is EMPTY OR resolutiondate >= "{scope.start_date}")',
    )


def jql_closed_during_period(scope: ScopeParams) -> str:
    """The "Closed/Cancelled (C)" column: resolved during this period,
    regardless of when the issue was originally created."""
    return _jql(
        scope.project_key,
        f'resolutiondate >= "{scope.start_date}" AND resolutiondate <= "{scope.end_date}"',
    )


def jql_fiscal_year_trend(project_key: str, as_of: date) -> str:
    """Full fiscal-year (Apr-Mar) issue set for the monthly trend tables.
    Fetched once per fiscal year and bucketed client-side by month, rather
    than firing 12 separate queries."""
    bounds = fiscal_year_bounds(as_of)
    return _jql(
        project_key,
        f'created >= "{bounds.start}" AND created <= "{bounds.end}"',
    )
