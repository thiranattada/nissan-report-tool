"""One function per report section. Each pulls pre-aggregated data from
reports/common/aggregations.py and writes it via table_writer — no Jira or
raw-issue logic lives here.

Known simplifications that need confirmation against the real Nissan Jira
project before this is trusted for a real client report (tracked as open
plan items / follow-ups, not bugs):
  - The exact "Category" field values (Failure/Inquiry/Service Request/
    Problem Management/Enhancement/Change-Release Management) are assumed;
    confirm against the live custom field's configured options.
  - The two "Top 5 Inquiry" tables split Inquiry issues along two different
    dimensions in the real report (e.g. "Operation inquiry" vs "Application")
    but no single Jira field for that split was confirmed yet — both use
    `route_cause` as a stand-in grouping key pending that confirmation.
  - Detail tables' "Plan Date" / "Actual Date" columns aren't backed by a
    known Jira field yet and are left blank.
"""

from app.jira.models import Issue, ScopeDataBundle
from app.reports.common import aggregations as agg
from app.reports.common import messages
from app.reports.common.scope import fiscal_year_label
from app.reports.pptx.table_map import TABLE_MAP
from app.reports.pptx.table_writer import get_table, write_rows


def _dedup(issues: list[Issue]) -> list[Issue]:
    return list({issue.key: issue for issue in issues}.values())


def build_incident_summary(prs, bundle: ScopeDataBundle) -> None:
    table = get_table(prs, *TABLE_MAP["incident_summary"])
    counts = agg.incident_summary_counts(bundle)

    incident_row = [
        "1. Incident Summary\n" + "\n".join(agg.INCIDENT_SUB_CATEGORIES),
        "\n".join(str(counts[c].carry_over) for c in agg.INCIDENT_SUB_CATEGORIES),
        "\n".join(str(counts[c].started) for c in agg.INCIDENT_SUB_CATEGORIES),
        "\n".join(str(counts[c].closed) for c in agg.INCIDENT_SUB_CATEGORIES),
        "\n".join(str(counts[c].on_process) for c in agg.INCIDENT_SUB_CATEGORIES),
    ]
    other_labels = ["2. Problem MGMT", "3. Enhancement (Change request)", "4. Change/Release MGM"]
    rows = [incident_row]
    for label, category in zip(other_labels, agg.OTHER_CATEGORIES):
        c = counts[category]
        rows.append([label, str(c.carry_over), str(c.started), str(c.closed), str(c.on_process)])

    write_rows(table, rows, start_row=2)


def build_module_breakdown(prs, bundle: ScopeDataBundle) -> None:
    table = get_table(prs, *TABLE_MAP["module_breakdown"])
    counts = agg.module_breakdown(bundle.current_period)
    rows = [[str(i + 1), module, str(count)] for i, (module, count) in enumerate(counts)]
    write_rows(table, rows, start_row=1)


def _build_trend_table(prs, table_name: str, bundle: ScopeDataBundle, category: str) -> None:
    table = get_table(prs, *TABLE_MAP[table_name])
    counts = agg.fiscal_month_trend(bundle.fiscal_year_trend, category)
    label = fiscal_year_label(bundle.scope.end_date)
    write_rows(table, [[label, *[str(c) for c in counts]]], start_row=1)


def _build_top5(prs, table_name: str, bundle: ScopeDataBundle, category: str) -> None:
    table = get_table(prs, *TABLE_MAP[table_name])
    capacity = len(table.rows) - 1
    issues = [i for i in bundle.current_period if i.category == category]
    top = agg.top_n_by(issues, lambda i: i.route_cause, n=capacity)
    rows = [[str(i + 1), label, str(count)] for i, (label, count) in enumerate(top)]
    write_rows(table, rows, start_row=1)


def _build_detail_table(prs, table_name: str, issues: list[Issue], empty_message: str) -> None:
    table = get_table(prs, *TABLE_MAP[table_name])
    rows = [
        [
            str(i + 1),
            issue.created.date().isoformat() if issue.created else "",
            (issue.components[0] if issue.components else ""),
            issue.summary,
            issue.route_cause or "",
            issue.countermeasure or "",
            issue.status,
            "",  # Plan Date: no confirmed source field yet
        ]
        for i, issue in enumerate(issues)
    ]
    write_rows(table, rows, start_row=1, empty_message=empty_message)


def build_inquiry_section(prs, bundle: ScopeDataBundle) -> None:
    _build_trend_table(prs, "trend_inquiry", bundle, "Inquiry")
    _build_top5(prs, "top5_inquiry_a", bundle, "Inquiry")
    _build_top5(prs, "top5_inquiry_b", bundle, "Inquiry")
    _build_detail_table(
        prs,
        "inquiry_detail_carryover_closed",
        [i for i in _dedup(bundle.carry_over_closed) if i.category == "Inquiry"],
        messages.NO_CARRY_OVER_FROM_LAST_MONTH,
    )
    _build_detail_table(
        prs,
        "inquiry_detail_carryover_open",
        [i for i in _dedup(bundle.carry_over_open) if i.category == "Inquiry"],
        messages.NO_CARRY_OVER_TO_NEXT_MONTH,
    )


def build_service_request_section(prs, bundle: ScopeDataBundle) -> None:
    _build_trend_table(prs, "trend_service_request", bundle, "Service Request")
    _build_top5(prs, "top5_service_request", bundle, "Service Request")
    _build_detail_table(
        prs,
        "service_request_detail_carryover_closed",
        [i for i in _dedup(bundle.carry_over_closed) if i.category == "Service Request"],
        messages.NO_CARRY_OVER_FROM_LAST_MONTH,
    )
    _build_detail_table(
        prs,
        "service_request_detail_carryover_open",
        [i for i in _dedup(bundle.carry_over_open) if i.category == "Service Request"],
        messages.NO_CARRY_OVER_TO_NEXT_MONTH,
    )


def build_failure_section(prs, bundle: ScopeDataBundle) -> None:
    _build_trend_table(prs, "trend_failure", bundle, "Failure")

    table = get_table(prs, *TABLE_MAP["failure_detail"])
    failures = _dedup(
        [i for i in bundle.current_period if i.category == "Failure"]
        + [i for i in bundle.closed_during_period if i.category == "Failure"]
    )
    rows = [
        [
            issue.impact_level or "",
            issue.category or "",
            issue.summary,
            issue.route_cause or "",
            issue.countermeasure or "",
            issue.created.strftime("%d/%b/%y %I:%M %p") if issue.created else "",
            issue.status,
            issue.resolved.date().isoformat() if issue.resolved else "",
        ]
        for issue in failures
    ]
    write_rows(table, rows, start_row=1, empty_message=messages.NO_FAILURE_THIS_MONTH)


def build_change_request(prs, bundle: ScopeDataBundle) -> None:
    table = get_table(prs, *TABLE_MAP["change_request"])
    issues = [i for i in bundle.current_period if i.category == "Enhancement"]
    rows = [
        [str(i + 1), issue.key, issue.summary, (issue.components[0] if issue.components else ""), issue.reporter or "", "", "", issue.status]
        for i, issue in enumerate(issues)
    ]
    write_rows(table, rows, start_row=1, empty_message=messages.NO_CHANGE_REQUEST_THIS_MONTH)


def build_problem_management(prs, bundle: ScopeDataBundle) -> None:
    table = get_table(prs, *TABLE_MAP["problem_management"])
    issues = [i for i in bundle.current_period if i.category == "Problem Management"]
    rows = [
        [str(i + 1), issue.key, (issue.components[0] if issue.components else ""), issue.summary, issue.route_cause or "", "", issue.countermeasure or "", "", ""]
        for i, issue in enumerate(issues)
    ]
    write_rows(table, rows, start_row=1, empty_message=messages.NO_PROBLEM_THIS_PERIOD)


def build_change_release_management(prs, bundle: ScopeDataBundle) -> None:
    table = get_table(prs, *TABLE_MAP["change_release_management"])
    counts = agg.incident_summary_counts(bundle)["Change/Release Management"]
    label = fiscal_year_label(bundle.scope.end_date)
    write_rows(
        table,
        [[label, str(counts.carry_over), str(counts.started), str(counts.closed), str(counts.on_process)]],
        start_row=1,
    )


def build_all_sections(prs, bundle: ScopeDataBundle) -> None:
    build_incident_summary(prs, bundle)
    build_module_breakdown(prs, bundle)
    build_inquiry_section(prs, bundle)
    build_service_request_section(prs, bundle)
    build_failure_section(prs, bundle)
    build_change_request(prs, bundle)
    build_problem_management(prs, bundle)
    build_change_release_management(prs, bundle)
