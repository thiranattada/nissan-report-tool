from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from app.jira import fields as F


@dataclass
class Issue:
    """A flattened view of the Jira fields we care about, plus the raw payload
    for anything not explicitly modeled (used by the Excel raw-export sheet)."""

    key: str
    summary: str
    issue_type: str
    status: str
    priority: Optional[str]
    created: datetime
    resolved: Optional[datetime]
    assignee: Optional[str]
    reporter: Optional[str]
    components: list[str]
    labels: list[str]
    route_cause: Optional[str]
    countermeasure: Optional[str]
    impact_level: Optional[str]
    category: Optional[str]
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, payload: dict) -> "Issue":
        f = payload.get("fields", {})

        def _text(value):
            if value is None:
                return None
            if isinstance(value, dict):
                return value.get("name") or value.get("value") or value.get("displayName")
            return value

        def _parse_dt(value):
            if not value:
                return None
            # Jira Cloud returns e.g. "2026-05-27T12:18:00.000+0700"
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

        return cls(
            key=payload["key"],
            summary=f.get("summary") or "",
            issue_type=_text(f.get("issuetype")) or "",
            status=_text(f.get("status")) or "",
            priority=_text(f.get("priority")),
            created=_parse_dt(f.get("created")),
            resolved=_parse_dt(f.get("resolutiondate")),
            assignee=_text(f.get("assignee")),
            reporter=_text(f.get("reporter")),
            components=[c.get("name") for c in (f.get("components") or [])],
            labels=list(f.get("labels") or []),
            route_cause=_text(f.get(F.FIELD_ROUTE_CAUSE)),
            countermeasure=_text(f.get(F.FIELD_COUNTERMEASURE)),
            impact_level=_text(f.get(F.FIELD_IMPACT_LEVEL)),
            category=_text(f.get(F.FIELD_CATEGORY)),
            raw=f,
        )


@dataclass
class ScopeParams:
    """The reporting window the user picked on the web form."""

    start_date: date
    end_date: date
    project_key: str
    sprint_id: Optional[str] = None  # reserved for future sprint-based scope


@dataclass
class ScopeDataBundle:
    """Everything both the Excel and PPT generators need, fetched once."""

    scope: ScopeParams
    current_period: list[Issue]  # created within this period ("Started" / B)
    carry_over_closed: list[Issue]  # opened before this period, closed during it (detail table)
    carry_over_open: list[Issue]  # opened before/during this period, still open at period end (detail table)
    open_at_period_start: list[Issue]  # unresolved as of period start ("Carry over" / A)
    closed_during_period: list[Issue]  # resolved during this period, any creation date ("Closed/Cancelled" / C)
    fiscal_year_trend: list[Issue]  # full fiscal-year issue set, for monthly trend tables
