from app.jira import fields as F
from app.jira import queries as Q
from app.jira.client import JiraClient
from app.jira.models import Issue, ScopeDataBundle, ScopeParams


class JiraDataService:
    """The single shared entry point both the Excel and PPT generators pull
    from — neither generator talks to JiraClient or builds JQL directly."""

    def __init__(self, client: JiraClient):
        self.client = client

    def _run(self, jql: str) -> list[Issue]:
        return [Issue.from_api(payload) for payload in self.client.search(jql, F.ALL_FIELDS)]

    def fetch_current_period(self, scope: ScopeParams) -> list[Issue]:
        return self._run(Q.jql_current_period(scope))

    def fetch_carry_over_closed(self, scope: ScopeParams) -> list[Issue]:
        return self._run(Q.jql_carry_over_closed(scope))

    def fetch_carry_over_open(self, scope: ScopeParams) -> list[Issue]:
        return self._run(Q.jql_carry_over_open(scope))

    def fetch_open_at_period_start(self, scope: ScopeParams) -> list[Issue]:
        return self._run(Q.jql_open_at_period_start(scope))

    def fetch_closed_during_period(self, scope: ScopeParams) -> list[Issue]:
        return self._run(Q.jql_closed_during_period(scope))

    def fetch_fiscal_year_trend(self, scope: ScopeParams) -> list[Issue]:
        jql = Q.jql_fiscal_year_trend(scope.project_key, scope.end_date)
        return self._run(jql)

    def fetch_full_scope_bundle(self, scope: ScopeParams) -> ScopeDataBundle:
        """One fetch, shared by both output formats — avoids duplicating
        Jira query logic between the Excel and PPT builders."""
        return ScopeDataBundle(
            scope=scope,
            current_period=self.fetch_current_period(scope),
            carry_over_closed=self.fetch_carry_over_closed(scope),
            carry_over_open=self.fetch_carry_over_open(scope),
            open_at_period_start=self.fetch_open_at_period_start(scope),
            closed_during_period=self.fetch_closed_during_period(scope),
            fiscal_year_trend=self.fetch_fiscal_year_trend(scope),
        )
